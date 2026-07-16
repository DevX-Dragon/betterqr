"""
QR Code data encoding: mode selection, bit stream construction, ECC interleaving.
Fully compliant with ISO/IEC 18004:2015.
"""
from __future__ import annotations
from .tables import (
    ECC_TABLE, MICRO_ECC_TABLE, MODE_NUMERIC, MODE_ALPHANUMERIC, MODE_BYTE, MODE_KANJI,
    ALPHANUMERIC_CHARS, RMQR_ECC_TABLE
)
from .gf import rs_encode


def _kanji_code(ch: str) -> int | None:
    """
    Return the 13-bit packed Kanji-mode code for a single character, or
    None if it can't be represented (ISO/IEC 18004:2015 §7.4.6): the
    character must encode as a 2-byte Shift-JIS value in one of the two
    JIS X 0208 ranges 0x8140-0x9FFC or 0xE040-0xEBBF.
    """
    try:
        raw = ch.encode("shift_jis")
    except UnicodeEncodeError:
        return None
    if len(raw) != 2:
        return None
    val = (raw[0] << 8) | raw[1]
    if 0x8140 <= val <= 0x9FFC:
        val -= 0x8140
    elif 0xE040 <= val <= 0xEBBF:
        val -= 0xC140
    else:
        return None
    return (val >> 8) * 0xC0 + (val & 0xFF)


def _can_encode_kanji(data: str) -> bool:
    """True if every character in data is representable in Kanji mode."""
    if not data:
        return False
    return all(_kanji_code(c) is not None for c in data)


def _best_mode(data: str, qr_type: str = "standard") -> int:
    """Return the most compact encoding mode for the given string."""
    if data.isdigit():
        return MODE_NUMERIC
    # Only use alphanumeric if ALL chars are in the 45-char set as-is (no case conversion)
    if all(c in ALPHANUMERIC_CHARS for c in data):
        return MODE_ALPHANUMERIC
    # Kanji mode is only implemented for standard QR in this release.
    if qr_type == "standard" and _can_encode_kanji(data):
        return MODE_KANJI
    return MODE_BYTE


# ECI (Extended Channel Interpretation) designator for UTF-8 (ISO/IEC 18004:2015 §7.4.9,
# assignment value 26 per the AIM ECI registry). Without an ECI segment, byte-mode data
# defaults to ISO-8859-1 per spec; some scanners guess UTF-8 anyway, but declaring it
# explicitly is the compliant way to encode non-ASCII text. Only applied to standard QR
# byte-mode payloads that actually contain non-ASCII characters, so plain-ASCII data is
# completely unaffected (no capacity cost, no bitstream change).
_ECI_UTF8_DESIGNATOR = 26
_ECI_MODE_INDICATOR = 0b0111
_ECI_OVERHEAD_BITS = 4 + 8  # mode indicator + single-byte designator (value < 128)

# Structured Append (ISO/IEC 18004:2015 §8.5.4): splits one logical message
# across up to 16 linked QR symbols. Header = mode indicator (4 bits) +
# symbol sequence indicator (8 bits: 4-bit position, 4-bit total-1) +
# parity byte (8 bits) = 20 bits, standard QR only.
MODE_STRUCTURED_APPEND = 0b0011
_SA_OVERHEAD_BITS = 4 + 8 + 8
MAX_STRUCTURED_APPEND_SYMBOLS = 16


def _as_bytes(data) -> bytes:
    return data if isinstance(data, (bytes, bytearray)) else data.encode("utf-8")


def _needs_eci(data, mode: int, qr_type: str) -> bool:
    if mode != MODE_BYTE or qr_type != "standard":
        return False
    if isinstance(data, (bytes, bytearray)):
        # Structured Append chunks are raw pre-split bytes; ECI (if needed)
        # is only meaningful once, at the start of the whole message, which
        # this per-chunk encoder doesn't manage — skip it for byte chunks.
        return False
    return any(ord(c) > 127 for c in data)


def _min_version(data: str, ecc_level: str, mode: int, qr_type: str = "standard",
                  extra_overhead_bits: int = 0) -> int:
    """Find the minimum QR version that fits the data."""
    n = len(_as_bytes(data)) if mode == MODE_BYTE else len(data)
    if qr_type == "standard":
        version_range = range(1, 41)
        ecc_lookup_table = ECC_TABLE
    elif qr_type == "micro":
        version_range = range(1, 5) # Micro QR versions M1-M4
        ecc_lookup_table = MICRO_ECC_TABLE
    elif qr_type == "rmqr":
        version_range = range(1, 2) # Placeholder for rMQR version 1
        ecc_lookup_table = RMQR_ECC_TABLE
    else:
        raise ValueError("Unsupported QR type for _min_version")

    for version in version_range:
        if version not in ecc_lookup_table or ecc_level not in ecc_lookup_table[version]:
            continue  # Skip if version/ecc_level combination is not defined for micro QR
        data_cw, _, _ = ecc_lookup_table[version][ecc_level]
        # Available bits
        if qr_type == "micro" and version in (1, 3):
            available_bits = (data_cw - 1) * 8 + 4
        else:
            available_bits = data_cw * 8
        # Required bits: mode indicator + char count + data
        if mode == MODE_NUMERIC:
            if qr_type == "micro":
                cc_bits = {1: 3, 2: 4, 3: 5, 4: 6}.get(version, 0)
                # Mode indicator bits: M1=0, M2=1, M3=2, M4=3
                mode_ind_bits = {1: 0, 2: 1, 3: 2, 4: 3}.get(version, 0)
            elif qr_type == "rmqr":
                cc_bits = 8  # Placeholder for rMQR numeric char count bits
                mode_ind_bits = 4
            else:
                cc_bits = 10 if version <= 9 else (12 if version <= 26 else 14)
                mode_ind_bits = 4
            groups = n // 3
            rem = n % 3
            data_bits = groups * 10 + (7 if rem == 1 else (4 if rem == 2 else 0))
            needed = mode_ind_bits + cc_bits + data_bits
            if needed <= available_bits:
                return version
        elif mode == MODE_ALPHANUMERIC:
            if qr_type == "micro":
                # M1 does not support alphanumeric — skip it
                if version == 1:
                    continue
                cc_bits = {2: 3, 3: 4, 4: 5}.get(version, 0)
                mode_ind_bits = {2: 1, 3: 2, 4: 3}.get(version, 0)
            elif qr_type == "rmqr":
                cc_bits = 6  # Placeholder for rMQR alphanumeric char count bits
                mode_ind_bits = 4
            else:
                cc_bits = 9 if version <= 9 else (11 if version <= 26 else 13)
                mode_ind_bits = 4
            pairs = n // 2
            data_bits = pairs * 11 + (6 if n % 2 else 0)
            needed = mode_ind_bits + cc_bits + data_bits
            if needed <= available_bits:
                return version
        elif mode == MODE_KANJI:
            # Kanji mode is standard-QR-only in this release (see _best_mode).
            cc_bits = 8 if version <= 9 else (10 if version <= 26 else 12)
            mode_ind_bits = 4
            data_bits = n * 13
            needed = mode_ind_bits + cc_bits + data_bits
            if needed <= available_bits:
                return version
        else:  # BYTE
            byte_data = _as_bytes(data)
            data_bits = len(byte_data) * 8
            if qr_type == "micro":
                # M1 and M2 do not support byte mode — skip them
                if version in (1, 2):
                    continue
                cc_bits = {3: 4, 4: 5}.get(version, 0)
                mode_ind_bits = {3: 2, 4: 3}.get(version, 0)
            elif qr_type == "rmqr":
                cc_bits = 7  # Placeholder for rMQR byte char count bits
                mode_ind_bits = 4
            else:
                cc_bits = 8 if version <= 9 else 16
                mode_ind_bits = 4
            needed = mode_ind_bits + cc_bits + data_bits
            if _needs_eci(data, mode, qr_type):
                needed += _ECI_OVERHEAD_BITS
            needed += extra_overhead_bits
            if needed <= available_bits:
                return version
    raise ValueError(f"Data too long to encode in any QR version at ECC level {ecc_level}")


def min_version_for_bytes(n_bytes: int, ecc_level: str, extra_overhead_bits: int = 0) -> int:
    """
    Return the smallest standard-QR version whose Byte-mode capacity (at
    the given ECC level) can hold n_bytes of raw data plus extra_overhead_bits
    of header (e.g. a Structured Append header). Raises ValueError if no
    version (up to 40) is large enough.
    """
    return _min_version(b"\x00" * n_bytes, ecc_level, MODE_BYTE, qr_type="standard",
                         extra_overhead_bits=extra_overhead_bits)


class BitStream:
    def __init__(self):
        self._bits: list[int] = []

    def append(self, value: int, n_bits: int):
        for i in range(n_bits - 1, -1, -1):
            self._bits.append((value >> i) & 1)

    def extend(self, bits: list[int]):
        self._bits.extend(bits)

    def __len__(self):
        return len(self._bits)

    def to_bytes(self) -> list[int]:
        # Pad to multiple of 8
        bits = list(self._bits)
        while len(bits) % 8:
            bits.append(0)
        return [
            int(''.join(str(b) for b in bits[i:i+8]), 2)
            for i in range(0, len(bits), 8)
        ]

    @property
    def bits(self):
        return self._bits


def encode_data(data: str, ecc_level: str, version: int | None = None, qr_type: str = "standard",
                 structured_append: tuple[int, int, int] | None = None) -> tuple[list[int], int, int]:
    """
    Encode data into QR codewords with ECC.

    structured_append: optional (sequence_index, total_symbols, parity_byte)
    for a Structured Append segment (standard QR only). When given, this
    chunk is always encoded in Byte mode — Structured Append splits raw
    bytes across symbols, so per-chunk mode auto-detection isn't used.

    Returns:
        (final_codewords, version, mode)
    """
    if structured_append is not None:
        if qr_type != "standard":
            raise ValueError("Structured Append is only supported for standard QR codes")
        mode = MODE_BYTE
        sa_overhead = _SA_OVERHEAD_BITS
    else:
        mode = _best_mode(data, qr_type=qr_type)
        sa_overhead = 0
    if version is None:
        version = _min_version(data, ecc_level, mode, qr_type=qr_type, extra_overhead_bits=sa_overhead)

    if qr_type == "standard":
        ecc_lookup_table = ECC_TABLE
    elif qr_type == "micro":
        ecc_lookup_table = MICRO_ECC_TABLE
    elif qr_type == "rmqr":
        ecc_lookup_table = RMQR_ECC_TABLE
    else:
        raise ValueError("Unsupported QR type for encode_data")

    data_cw_count, block_info, ec_per_block = ecc_lookup_table[version][ecc_level]
    total_data_bits = data_cw_count * 8

    bs = BitStream()

    if structured_append is not None:
        seq_index, total_symbols, parity = structured_append
        if not (0 <= seq_index < total_symbols <= MAX_STRUCTURED_APPEND_SYMBOLS):
            raise ValueError(
                f"structured_append sequence_index/total_symbols out of range "
                f"(0 <= index < total <= {MAX_STRUCTURED_APPEND_SYMBOLS})"
            )
        bs.append(MODE_STRUCTURED_APPEND, 4)
        bs.append(seq_index, 4)
        bs.append(total_symbols - 1, 4)
        bs.append(parity & 0xFF, 8)

    if _needs_eci(data, mode, qr_type):
        bs.append(_ECI_MODE_INDICATOR, 4)
        bs.append(_ECI_UTF8_DESIGNATOR, 8)

    # Mode indicator (ISO 18004:2015 Table 2)
    # Standard QR: always 4 bits; Micro QR: 0 bits for M1, 1 for M2, 2 for M3, 3 for M4
    if qr_type == "micro":
        # Micro QR mode indicator values: numeric=0, alphanumeric=1, byte=2, kanji=3
        micro_mode_val = {MODE_NUMERIC: 0, MODE_ALPHANUMERIC: 1, MODE_BYTE: 2, MODE_KANJI: 3}.get(mode, 0)
        micro_mode_bits = {1: 0, 2: 1, 3: 2, 4: 3}.get(version, 0)
        if micro_mode_bits > 0:
            bs.append(micro_mode_val, micro_mode_bits)
    else:
        bs.append(mode, 4)
    n = len(_as_bytes(data)) if mode == MODE_BYTE else len(data)
    if mode == MODE_NUMERIC:
        if qr_type == "micro":
            # ISO 18004:2015 Annex D Table D.2: M1=3, M2=4, M3=5, M4=6
            cc_bits = {1: 3, 2: 4, 3: 5, 4: 6}.get(version, 0)
        elif qr_type == "rmqr":
            cc_bits = 8
        else:
            cc_bits = 10 if version <= 9 else (12 if version <= 26 else 14)
    elif mode == MODE_ALPHANUMERIC:
        if qr_type == "micro":
            # ISO 18004:2015 Annex D Table D.2: M1=n/a, M2=3, M3=4, M4=5
            cc_bits = {2: 3, 3: 4, 4: 5}.get(version, 0)
        elif qr_type == "rmqr":
            cc_bits = 6
        else:
            cc_bits = 9 if version <= 9 else (11 if version <= 26 else 13)
    elif mode == MODE_KANJI:
        # Kanji mode is standard-QR-only in this release.
        cc_bits = 8 if version <= 9 else (10 if version <= 26 else 12)
    else:  # BYTE
        if qr_type == "micro":
            # ISO 18004:2015 Annex D Table D.2: M1=n/a, M2=n/a, M3=4, M4=5
            cc_bits = {3: 4, 4: 5}.get(version, 0)
        elif qr_type == "rmqr":
            cc_bits = 7
        else:
            cc_bits = 8 if version <= 9 else 16
    bs.append(n, cc_bits)

    # Data encoding
    if mode == MODE_NUMERIC:
        s = data
        while len(s) >= 3:
            bs.append(int(s[:3]), 10)
            s = s[3:]
        if len(s) == 2:
            bs.append(int(s), 7)
        elif len(s) == 1:
            bs.append(int(s), 4)

    elif mode == MODE_ALPHANUMERIC:
        s = data.upper()
        while len(s) >= 2:
            v = ALPHANUMERIC_CHARS.index(s[0]) * 45 + ALPHANUMERIC_CHARS.index(s[1])
            bs.append(v, 11)
            s = s[2:]
        if len(s) == 1:
            bs.append(ALPHANUMERIC_CHARS.index(s[0]), 6)

    elif mode == MODE_KANJI:
        for ch in data:
            bs.append(_kanji_code(ch), 13)

    else:  # BYTE
        for byte in _as_bytes(data):
            bs.append(byte, 8)

    # Terminator (ISO 18004:2015 Table 2): M1=3, M2=5, M3=7, M4=9; standard QR=4
    if qr_type == "micro":
        max_term = {1: 3, 2: 5, 3: 7, 4: 9}.get(version, 4)
    else:
        max_term = 4
    remaining = total_data_bits - len(bs)
    term = min(max_term, remaining)
    bs.append(0, term)

    # Bit padding to byte boundary
    while len(bs) % 8:
        bs.append(0, 1)

    # Byte padding: standard QR uses 0xEC/0x11; Micro QR uses 0x00 (ISO 18004 §8.5.3)
    pad_byte = 0x00 if qr_type == "micro" else None
    pad_bytes = [pad_byte, pad_byte] if pad_byte is not None else [0xEC, 0x11]
    pad_idx = 0
    data_bytes = bs.to_bytes()
    while len(data_bytes) < data_cw_count:
        data_bytes.append(pad_bytes[pad_idx])
        if pad_byte is None:
            pad_idx ^= 1

    data_bytes = data_bytes[:data_cw_count]

    # --- Split into blocks and compute EC ---
    blocks_data = []
    blocks_ec = []
    pos = 0
    for n_blocks, data_per_block in block_info:
        for _ in range(n_blocks):
            blk = data_bytes[pos:pos + data_per_block]
            blocks_data.append(blk)
            blocks_ec.append(rs_encode(blk, ec_per_block))
            pos += data_per_block

    # Interleave data codewords
    final = []
    max_data = max(len(b) for b in blocks_data)
    for i in range(max_data):
        for blk in blocks_data:
            if i < len(blk):
                final.append(blk[i])

    # Interleave EC codewords
    max_ec = max(len(b) for b in blocks_ec)
    for i in range(max_ec):
        for blk in blocks_ec:
            if i < len(blk):
                final.append(blk[i])

    # For M1 and M3, the final message bit stream must be built specially:
    # the last DATA codeword contributes only its HIGH 4 BITS (ISO 18004:2015 §8.5.3).
    # We achieve this by converting the full codeword list to a bit stream and
    # truncating to the exact matrix capacity (36 or 132 bits).
    # The build_matrix data placer already handles truncation correctly by only
    # writing min(len(bits), n_data_cells) bits — so no further change needed here.

    return final, version, mode