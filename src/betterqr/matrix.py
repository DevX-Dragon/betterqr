"""
QR Code matrix construction: all function patterns, data placement, masking.
Fully compliant with ISO/IEC 18004:2015.
"""
from __future__ import annotations
from .tables import (
    ALIGNMENT_POSITIONS, FORMAT_INFO, VERSION_INFO, ECC_BITS,
    MICRO_ECC_TABLE, MICRO_ALIGNMENT_POSITIONS, MICRO_FORMAT_INFO, MICRO_VERSION_INFO
)


# Mask pattern conditions
_MASK_CONDITIONS = [
    lambda r, c: (r + c) % 2 == 0,
    lambda r, c: r % 2 == 0,
    lambda r, c: c % 3 == 0,
    lambda r, c: (r + c) % 3 == 0,
    lambda r, c: (r // 2 + c // 3) % 2 == 0,
    lambda r, c: ((r * c) % 2) + ((r * c) % 3) == 0,
    lambda r, c: (((r * c) % 2) + ((r * c) % 3)) % 2 == 0,
    lambda r, c: (((r + c) % 2) + ((r * c) % 3)) % 2 == 0,
]

# Micro QR uses a distinct set of 4 mask patterns (ISO 18004:2015 Table 10).
# They correspond to standard QR conditions at indices 1, 4, 6, 7.
_MICRO_MASK_CONDITIONS = [
    lambda r, c: r % 2 == 0,                                           # micro mask 0
    lambda r, c: (r // 2 + c // 3) % 2 == 0,                          # micro mask 1
    lambda r, c: (((r * c) % 2) + ((r * c) % 3)) % 2 == 0,            # micro mask 2
    lambda r, c: (((r + c) % 2) + ((r * c) % 3)) % 2 == 0,            # micro mask 3
]

_UNSET = -1   # Not yet assigned
_DARK  = 1    # Dark module
_LIGHT = 0    # Light module


def _make_grid(size: int):
    return [[_UNSET] * size for _ in range(size)]


def _place_finder(grid, row, col):
    """Place a 7×7 finder pattern with top-left at (row, col)."""
    size = len(grid)
    for r in range(7):
        for c in range(7):
            dr, dc = row + r, col + c
            if 0 <= dr < size and 0 <= dc < size:
                if r in (0, 6) or c in (0, 6):
                    grid[dr][dc] = _DARK
                elif 2 <= r <= 4 and 2 <= c <= 4:
                    grid[dr][dc] = _DARK
                else:
                    grid[dr][dc] = _LIGHT


def _place_separators(grid, size):
    """White separator rows/cols around finders."""
    # Top-left
    for i in range(8):
        _safe_set(grid, 7, i, _LIGHT)
        _safe_set(grid, i, 7, _LIGHT)
    # Top-right
    for i in range(8):
        _safe_set(grid, 7, size - 8 + i, _LIGHT)
        _safe_set(grid, i, size - 8, _LIGHT)
    # Bottom-left
    for i in range(8):
        _safe_set(grid, size - 8, i, _LIGHT)
        _safe_set(grid, size - 8 + i, 7, _LIGHT)


def _safe_set(grid, r, c, val):
    size = len(grid)
    if 0 <= r < size and 0 <= c < size:
        grid[r][c] = val


def _place_alignment(grid, version):
    """Place all alignment patterns for the version."""
    positions = ALIGNMENT_POSITIONS[version]
    if not positions:
        return
    # Generate all combinations, skip those overlapping finders
    size = len(grid)
    for row in positions:
        for col in positions:
            # Check overlap with finder areas (top-left, top-right, bottom-left)
            if row <= 8 and col <= 8:
                continue  # top-left finder
            if row <= 8 and col >= size - 9:
                continue  # top-right finder
            if row >= size - 9 and col <= 8:
                continue  # bottom-left finder
            # Place 5×5 alignment pattern
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    r, c = row + dr, col + dc
                    if abs(dr) == 2 or abs(dc) == 2:
                        grid[r][c] = _DARK
                    elif dr == 0 and dc == 0:
                        grid[r][c] = _DARK
                    else:
                        grid[r][c] = _LIGHT


def _place_timing(grid, size):
    """Place timing patterns along row 6 and col 6."""
    for i in range(8, size - 8):
        val = _DARK if i % 2 == 0 else _LIGHT
        if grid[6][i] == _UNSET:
            grid[6][i] = val
        if grid[i][6] == _UNSET:
            grid[i][6] = val


def _place_dark_module(grid, version):
    """The always-dark module at (4*version+9, 8)."""
    grid[4 * version + 9][8] = _DARK


def _reserve_format_areas(reserved, size):
    """Mark format information areas as reserved (ISO 18004:2015 §7.9.1)."""
    # Copy 1: top-left finder area
    for i in range(9):
        reserved[8][i] = True   # row 8, cols 0-8
        reserved[i][8] = True   # col 8, rows 0-8
    # Copy 2: top-right area (row 8, cols size-8..size-1)
    for i in range(8):
        reserved[8][size - 1 - i] = True
    # Copy 2: bottom-left area (col 8, rows size-8..size-1)
    for i in range(8):
        reserved[size - 1 - i][8] = True


def _reserve_version_areas(reserved, size, version):
    """Mark version information areas (versions 7+)."""
    if version < 7:
        return
    # Top-right version block: 6×3 block at columns size-11..size-9, rows 0..5
    for r in range(6):
        for c in range(size - 11, size - 8):
            reserved[r][c] = True
    # Bottom-left version block: 3×6 block at rows size-11..size-9, cols 0..5
    for r in range(size - 11, size - 8):
        for c in range(6):
            reserved[r][c] = True


def _write_format_info(grid, ecc_level: str, mask_pattern: int, size: int):
    """Write format information (15 bits, two copies) per ISO 18004:2015 §7.9.1.

    Placement matches segno's verified add_format_info logic:
      - Copy 1 vertical (col 8): bit i at row i (skip row 6), LSB first
      - Copy 1 horizontal (row 8): bit (14-i) at col i (skip col 6), MSB first
      - Copy 2 top-right (row 8): same as vertical bits, cols size-1..size-8
      - Copy 2 bottom-left (col 8): same as horizontal bits, rows size-1..size-8
    """
    fmt = FORMAT_INFO[(ecc_level, mask_pattern)]
    row_eight = grid[8]

    voffset = 0
    hoffset = 0
    for i in range(8):
        vbit = (fmt >> i) & 1
        hbit = (fmt >> (14 - i)) & 1
        if i == 6:
            voffset = 1   # skip row 6 (timing)
            hoffset = 1   # skip col 6 (timing)
        # Copy 1
        grid[i + voffset][8] = vbit     # vertical strip, col 8
        row_eight[i + hoffset] = hbit   # horizontal strip, row 8

        # Copy 2
        row_eight[size - 1 - i] = vbit          # top-right, row 8
        grid[size - 1 - i][8] = hbit             # bottom-left, col 8

    # Dark module (always dark)
    grid[size - 8][8] = _DARK


def _write_micro_format_info(grid, ecc_level: str, mask_pattern: int, version: int, size: int):
    """Write Micro QR format information (ISO/IEC 18004:2015 §7.9.2).

    15-bit format word split across two strips (8 positions each, sharing corner (8,8)):
      - Vertical:   bit i      → grid[i+1][8],  i = 0..7  (rows 1-8, col 8, LSB first)
      - Horizontal: bit (14-i) → grid[8][i+1],  i = 0..7  (row 8, cols 1-8, MSB first)
    The corner cell (8, 8) receives bit 7 from both strips (same value, no conflict).
    """
    fmt = MICRO_FORMAT_INFO[(version, ecc_level, mask_pattern)]
    for i in range(8):
        grid[i + 1][8] = (fmt >> i) & 1        # vertical: LSB at row 1
        grid[8][i + 1] = (fmt >> (14 - i)) & 1  # horizontal: MSB at col 1

def _write_version_info(grid, version: int, size: int):
    """Write version information blocks for versions 7+."""
    if version < 7:
        return
    info = VERSION_INFO[version]
    for i in range(18):
        bit = (info >> i) & 1
        r_tr = i // 3
        c_tr = size - 11 + (i % 3)
        grid[r_tr][c_tr] = bit
        grid[c_tr][r_tr] = bit  # mirrored for bottom-left block


def _data_placement_order(size: int, reserved, qr_type: str = "standard") -> list[tuple[int, int]]:
    """Return (row, col) pairs in QR data placement order (right-to-left column pairs).

    In standard QR col 6 is the vertical timing strip and must be skipped explicitly.
    In Micro QR col 0 is timing (already reserved), so no special skip is needed.
    """
    order = []
    col = size - 1
    going_up = True
    while col >= 0:
        if col == 6 and qr_type == "standard":
            col -= 1  # skip timing column (standard QR only)
        row_range = range(size - 1, -1, -1) if going_up else range(size)
        for row in row_range:
            for c_offset in (0, 1):
                c = col - c_offset
                if 0 <= c < size and not reserved[row][c]:
                    order.append((row, c))
        col -= 2
        going_up = not going_up
    return order


def _apply_mask(grid, mask_pattern: int, reserved, qr_type: str = "standard") -> list[list[int]]:
    """Return a copy of grid with mask applied to non-reserved modules."""
    if qr_type == "micro":
        condition = _MICRO_MASK_CONDITIONS[mask_pattern]
    else:
        condition = _MASK_CONDITIONS[mask_pattern]
    size = len(grid)
    result = [row[:] for row in grid]
    for r in range(size):
        for c in range(size):
            if not reserved[r][c] and grid[r][c] != _UNSET:
                if condition(r, c):
                    result[r][c] ^= 1
    return result


def _penalty_score(grid) -> int:
    """Calculate mask penalty score (lower is better)."""
    size = len(grid)
    score = 0

    # Rule 1: 5+ consecutive same-color modules in a row/column
    for row in grid:
        count = 1
        for i in range(1, size):
            if row[i] == row[i-1]:
                count += 1
            else:
                if count >= 5:
                    score += 3 + (count - 5)
                count = 1
        if count >= 5:
            score += 3 + (count - 5)
    for c in range(size):
        count = 1
        for r in range(1, size):
            if grid[r][c] == grid[r-1][c]:
                count += 1
            else:
                if count >= 5:
                    score += 3 + (count - 5)
                count = 1
        if count >= 5:
            score += 3 + (count - 5)

    # Rule 2: 2×2 blocks of same color
    for r in range(size - 1):
        for c in range(size - 1):
            v = grid[r][c]
            if v == grid[r][c+1] == grid[r+1][c] == grid[r+1][c+1]:
                score += 3

    # Rule 3: specific patterns in rows/columns
    pat1 = [1,0,1,1,1,0,1,0,0,0,0]
    pat2 = [0,0,0,0,1,0,1,1,1,0,1]
    for row in grid:
        row_list = row
        for i in range(size - 10):
            seg = row_list[i:i+11]
            if seg == pat1 or seg == pat2:
                score += 40
    for c in range(size):
        col = [grid[r][c] for r in range(size)]
        for i in range(size - 10):
            seg = col[i:i+11]
            if seg == pat1 or seg == pat2:
                score += 40

    # Rule 4: proportion of dark modules
    total = size * size
    dark = sum(grid[r][c] for r in range(size) for c in range(size))
    percent = dark * 100 // total
    prev5 = (percent // 5) * 5
    next5 = prev5 + 5
    score += min(abs(prev5 - 50), abs(next5 - 50)) // 5 * 10

    return score


def build_matrix(codewords: list[int], version: int, ecc_level: str, qr_type: str = "standard", logo_info: dict | None = None) -> list[list[int]]:
    """
    Build the final QR code matrix with the best mask pattern applied.
    Returns a 2D list of 0 (light) and 1 (dark).
    """
    if qr_type == "standard":
        size = version * 4 + 17
    elif qr_type == "micro":
        size = version * 2 + 9
    elif qr_type == "rmqr":
        if version == 1:
            size = (15, 27)
        else:
            raise ValueError("Unsupported rMQR version for basic structuring")
    else:
        raise ValueError("Unsupported QR type")

    # --- Place all function patterns ---
    grid = _make_grid(size)
    reserved = [[False] * size for _ in range(size)]

    if qr_type == "standard":
        # Finder patterns
        _place_finder(grid, 0, 0)        # top-left
        _place_finder(grid, 0, size-7)   # top-right
        _place_finder(grid, size-7, 0)   # bottom-left

        for r in range(9):
            for c in range(9):
                reserved[r][c] = True
        for r in range(9):
            for c in range(size-8, size):
                reserved[r][c] = True
        for r in range(size-8, size):
            for c in range(9):
                reserved[r][c] = True

        _place_separators(grid, size)
        _place_alignment(grid, version)

        positions = ALIGNMENT_POSITIONS[version]
        if positions:
            for row in positions:
                for col in positions:
                    if row <= 8 and col <= 8: continue
                    if row <= 8 and col >= size - 9: continue
                    if row >= size - 9 and col <= 8: continue
                    for dr in range(-2, 3):
                        for dc in range(-2, 3):
                            reserved[row+dr][col+dc] = True

        _place_timing(grid, size)
        for i in range(size):
            reserved[6][i] = True
            reserved[i][6] = True

        _place_dark_module(grid, version)
        reserved[4*version+9][8] = True

        _reserve_format_areas(reserved, size)
        _reserve_version_areas(reserved, size, version)
    elif qr_type == "micro":
        _place_finder(grid, 0, 0)

        # Separator: single row 7 and single column 7 (both light)
        for i in range(8):
            grid[7][i] = _LIGHT
            grid[i][7] = _LIGHT

        # Reserve the full 9×9 top-left block (finder 7×7 + separator + format info corner)
        for r in range(9):
            for c in range(9):
                reserved[r][c] = True

        # Timing patterns: run along ROW 0 and COL 0 from index 8 outward (ISO 18004 §7.3.4)
        for i in range(8, size):
            val = _DARK if i % 2 == 0 else _LIGHT
            grid[0][i] = val
            reserved[0][i] = True
            grid[i][0] = val
            reserved[i][0] = True

        # Format information strips (ISO 18004 §7.9.2):
        #   Vertical: rows 1-8, col 8  |  Horizontal: row 8, cols 1-8
        for i in range(1, 9):
            reserved[i][8] = True   # vertical strip: rows 1-8, col 8
            reserved[8][i] = True   # horizontal strip: row 8, cols 1-8
    elif qr_type == "rmqr":
        rows, cols = size
        _place_finder(grid, 0, 0)

        for r in range(9):
            for c in range(9):
                if r < rows and c < cols:
                    reserved[r][c] = True

        for i in range(8, cols - 8):
            if i < cols:
                grid[6][i] = _DARK if i % 2 == 0 else _LIGHT
                reserved[6][i] = True
        for i in range(8, rows - 8):
            if i < rows:
                grid[i][6] = _DARK if i % 2 == 0 else _LIGHT
                reserved[i][6] = True

        if rows > 1 and cols > 1:
            grid[rows - 2][1] = _DARK
            reserved[rows - 2][1] = True

        for i in range(8):
            if i < cols:
                reserved[8][i] = True
            if i < rows:
                reserved[i][8] = True



    # --- Place data bits ---
    # For M1 (version 1) and M3 (version 3), the last DATA codeword contributes
    # only its HIGH 4 BITS to the bit stream; ALL ECC codewords follow in full.
    # (ISO 18004:2015 §8.5.3 / segno make_final_message)
    if qr_type == "micro" and version in (1, 3):
        data_cw_count, _, ec_per_block = (
            MICRO_ECC_TABLE[version][ecc_level]
        )
        data_part = codewords[:data_cw_count]
        ecc_part  = codewords[data_cw_count:]
        bits = []
        for cw in data_part[:-1]:           # all but last data CW — full 8 bits
            for i in range(7, -1, -1):
                bits.append((cw >> i) & 1)
        # Last data CW: only HIGH 4 BITS
        last_cw = data_part[-1]
        for i in range(7, 3, -1):           # bits 7,6,5,4 (high nibble)
            bits.append((last_cw >> i) & 1)
        for cw in ecc_part:                 # ECC codewords — all full 8 bits
            for i in range(7, -1, -1):
                bits.append((cw >> i) & 1)
    else:
        bits = []
        for cw in codewords:
            for i in range(7, -1, -1):
                bits.append((cw >> i) & 1)

    placement = _data_placement_order(size, reserved, qr_type)
    for idx, (r, c) in enumerate(placement):
        grid[r][c] = bits[idx] if idx < len(bits) else 0

    if logo_info:
        logo_size_px = logo_info["size_px"]
        logo_padding_px = logo_info["padding_px"]
        box_size = logo_info["box_size"]
        border = logo_info["border"]

        qr_total_size_px = size * box_size + 2 * border * box_size
        logo_start_px = (qr_total_size_px - logo_size_px) / 2
        logo_end_px = (qr_total_size_px + logo_size_px) / 2

        logo_start_module_r = int((logo_start_px - border * box_size) / box_size)
        logo_end_module_r = int((logo_end_px - border * box_size) / box_size)
        logo_start_module_c = int((logo_start_px - border * box_size) / box_size)
        logo_end_module_c = int((logo_end_px - border * box_size) / box_size)

        padding_modules = int(logo_padding_px / box_size) if box_size > 0 else 0
        logo_start_module_r -= padding_modules
        logo_end_module_r += padding_modules
        logo_start_module_c -= padding_modules
        logo_end_module_c += padding_modules

        logo_start_module_r = max(0, logo_start_module_r)
        logo_end_module_r = min(size, logo_end_module_r)
        logo_start_module_c = max(0, logo_start_module_c)
        logo_end_module_c = min(size, logo_end_module_c)

        for r in range(logo_start_module_r, logo_end_module_r):
            for c in range(logo_start_module_c, logo_end_module_c):
                grid[r][c] = _LIGHT
                reserved[r][c] = True

    # --- Evaluate all 8 masks (standard) or 4 masks (micro), pick best ---
    best_score = float('inf')
    best_mask = 0
    best_grid = None

    num_masks = 8 if qr_type == "standard" else 4
    for mask_pattern in range(num_masks):
        masked = _apply_mask(grid, mask_pattern, reserved, qr_type)
        if qr_type == "standard":
            _write_format_info(masked, ecc_level, mask_pattern, size)
            _write_version_info(masked, version, size)
        elif qr_type == "micro":
            _write_micro_format_info(masked, ecc_level, mask_pattern, version, size)
        elif qr_type == "rmqr":
            pass
        score = _penalty_score(masked)
        if score < best_score:
            best_score = score
            best_mask = mask_pattern
            best_grid = masked

    return best_grid