"""
Terminal renderer for BetterQR.
Outputs QR codes to the terminal using Unicode block characters or plain ASCII.
"""
from __future__ import annotations


def render_terminal(
    matrix: list[list[int]],
    border: int = 2,
    invert: bool = False,
    style: str = "block",  # block | ascii | compact
) -> str:
    """
    Render QR code as a terminal string.

    Args:
        matrix: QR code matrix (1=dark, 0=light)
        border: quiet zone in modules
        invert: swap dark/light (useful for dark terminals)
        style: 'block' uses Unicode half-blocks (best quality),
               'ascii' uses # and space, 'compact' uses full blocks
    Returns:
        String to print to terminal
    """
    size = len(matrix)
    rows = []
    pad = " " * border

    if style == "compact":
        # Full block chars: █ = dark, space = light
        dark_char = "█" if not invert else " "
        light_char = " " if not invert else "█"
        top = pad + light_char * (size + 2 * border) + pad
        rows.append(top)
        for _ in range(border):
            rows.append(pad + light_char * (size + 2 * border))
        for r in range(size):
            line = pad
            for _ in range(border):
                line += light_char
            for c in range(size):
                val = matrix[r][c]
                if invert:
                    val = 1 - val
                line += dark_char if val else light_char
            for _ in range(border):
                line += light_char
            rows.append(line)
        for _ in range(border):
            rows.append(pad + light_char * (size + 2 * border))
        return "\n".join(rows)

    elif style == "ascii":
        dark_char = "##" if not invert else "  "
        light_char = "  " if not invert else "##"
        for _ in range(border):
            rows.append(light_char * (size + 2 * border))
        for r in range(size):
            line = light_char * border
            for c in range(size):
                val = matrix[r][c]
                if invert:
                    val = 1 - val
                line += dark_char if val else light_char
            line += light_char * border
            rows.append(line)
        for _ in range(border):
            rows.append(light_char * (size + 2 * border))
        return "\n".join(rows)

    else:  # block - uses half-block to pack 2 rows into 1 line
        # ▀ = top dark, ▄ = bottom dark, █ = both dark, ' ' = both light
        def char(top_dark: bool, bot_dark: bool, inv: bool) -> str:
            if inv:
                top_dark, bot_dark = not top_dark, not bot_dark
            if top_dark and bot_dark:
                return "█"
            elif top_dark:
                return "▀"
            elif bot_dark:
                return "▄"
            else:
                return " "

        total = size + 2 * border
        # Pad rows
        padded = []
        for _ in range(border):
            padded.append([0] * total)
        for r in range(size):
            row = [0] * border + [matrix[r][c] for c in range(size)] + [0] * border
            padded.append(row)
        for _ in range(border):
            padded.append([0] * total)

        # Pair up rows
        r = 0
        while r < len(padded):
            top_row = padded[r]
            bot_row = padded[r + 1] if r + 1 < len(padded) else [0] * total
            line = ""
            for c in range(total):
                line += char(bool(top_row[c]), bool(bot_row[c]), invert)
            rows.append(line)
            r += 2
        return "\n".join(rows)
