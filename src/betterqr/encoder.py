"""
QR Code data encoding: mode selection, bit stream construction, ECC interleaving.
Fully compliant with ISO/IEC 18004:2015.
"""
from __future__ import annotations
from .tables import (
    ECC_TABLE, MODE_NUMERIC, MODE_ALPHANUMERIC, MODE_BYTE,
    ALPHANUMERIC_CHARS
)
from .gf import rs_encode


def _best_mode(data: str) -> int:
    """Return the most compact encoding mode for the given string."""
    if data.isdigit():
        return MODE_NUMERIC
    # Only use alphanumeric if ALL chars are in the 45-char set as-is (no case conversion)
    if all(c in ALPHANUMERIC_CHARS for c in data):
        return MODE_ALPHANUMERIC
    return MODE_BYTE


def _min_version(data: str, ecc_level: str, mode: int) -> int:
    """Find the minimum QR version that fits the data."""
    n = len(data.encode('utf-8')) if mode == MODE_BYTE else len(data)
    for version in range(1, 41):
        data_cw, _, _ = ECC_TABLE[version][ecc_level]
        # Available bits
        available_bits = data_cw * 8
        # Required bits: mode indicator + char count + data
        if mode == MODE_NUMERIC:
            cc_bits = 10 if version <= 9 else (12 if version <= 26 else 14)
            if version <= 9:
                groups = n // 3
                rem = n % 3
                data_bits = groups * 10 + (7 if rem == 1 else (4 if rem == 2 else 0))
            else:
                groups = n // 3
                rem = n % 3
                data_bits = groups * 10 + (7 if rem == 1 else (4 if rem == 2 else 0))
            needed = 4 + cc_bits + data_bits
        elif mode == MODE_ALPHANUMERIC:
            cc_bits = 9 if version <= 9 else (11 if version <= 26 else 13)
            pairs = n // 2
            data_bits = pairs * 11 + (6 if n % 2 else 0)
            needed = 4 + cc_bits + data_bits
        else:  # BYTE
            cc_bits = 8 if version <= 9 else 16
            byte_data = data.encode('utf-8')
            data_bits = len(byte_data) * 8
            needed = 4 + cc_bits + data_bits
        if needed <= available_bits:
            return version
    raise ValueError(f"Data too long to encode in any QR version at ECC level {ecc_level}")


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


def encode_data(data: str, ecc_level: str, version: int | None = None) -> tuple[list[int], int, int]:
    """
    Encode data into QR codewords with ECC.

    Returns:
        (final_codewords, version, mode)
    """
    mode = _best_mode(data)
    if version is None:
        version = _min_version(data, ecc_level, mode)

    data_cw_count, block_info, ec_per_block = ECC_TABLE[version][ecc_level]
    total_data_bits = data_cw_count * 8

    bs = BitStream()

    # Mode indicator
    bs.append(mode, 4)

    # Character count indicator
    n = len(data.encode('utf-8')) if mode == MODE_BYTE else len(data)
    if mode == MODE_NUMERIC:
        cc_bits = 10 if version <= 9 else (12 if version <= 26 else 14)
    elif mode == MODE_ALPHANUMERIC:
        cc_bits = 9 if version <= 9 else (11 if version <= 26 else 13)
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

    else:  # BYTE
        for byte in data.encode('utf-8'):
            bs.append(byte, 8)

    # Terminator
    remaining = total_data_bits - len(bs)
    term = min(4, remaining)
    bs.append(0, term)

    # Bit padding to byte boundary
    while len(bs) % 8:
        bs.append(0, 1)

    # Byte padding
    pad_bytes = [0xEC, 0x11]
    pad_idx = 0
    data_bytes = bs.to_bytes()
    while len(data_bytes) < data_cw_count:
        data_bytes.append(pad_bytes[pad_idx])
        pad_idx ^= 1

    data_bytes = data_bytes[:data_cw_count]

    # --- Split into blocks and compute EC ---
    # Build list of (data_block, ec_block) pairs
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

    return final, version, mode
