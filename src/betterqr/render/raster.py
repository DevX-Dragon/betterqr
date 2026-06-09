"""
Raster renderer for BetterQR.
Outputs PNG/JPEG with full styling support.
Finder patterns are always rendered as squares (for maximum scannability).
"""
from __future__ import annotations
import io
import math

from ..extras.image_ops import _logo_ratio_limit


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    color = color.strip()
    if color.lower() == 'transparent':
        return (255, 255, 255)
    if color.startswith('#'):
        color = color[1:]
    if len(color) == 3:
        color = ''.join(c*2 for c in color)
    return (int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16))


def _is_transparent(color: str) -> bool:
    return color.strip().lower() == 'transparent'


def _lerp_color(c1: tuple, c2: tuple, t: float) -> tuple[int, int, int]:
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def _is_finder(r: int, c: int, size: int) -> bool:
    """True if (r,c) is inside a 7x7 finder pattern."""
    if r < 7 and c < 7:   return True
    if r < 7 and c >= size - 7: return True
    if r >= size - 7 and c < 7: return True
    return False


def render_png(
    matrix: list[list[int]],
    box_size: int = 10,
    border: int = 4,
    fill_color: str = "#000000",
    back_color: str = "#FFFFFF",
    module_shape: str = "square",
    gradient_color: str | None = None,
    gradient_dir: str = "diagonal",
    finder_color: str | None = None,
    logo_path: str | None = None,
    logo_ratio: float = 0.25,
    ecc_level: str | None = None,
    version: int | None = None,
    module_gap: float = 0.15,
    quiet_zone_color: str | None = None,
    format: str = "PNG",
) -> io.BytesIO:
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        raise ImportError("Pillow is required: pip install Pillow")

    size = len(matrix)
    total_px = (size + 2 * border) * box_size
    offset = border * box_size

    is_rgba = _is_transparent(back_color)
    bg_color = (255, 255, 255, 0) if is_rgba else _hex_to_rgb(back_color) + (255,)
    img = Image.new("RGBA", (total_px, total_px), bg_color)
    draw = ImageDraw.Draw(img)

    fill_rgb = _hex_to_rgb(fill_color)
    grad_rgb = _hex_to_rgb(gradient_color) if gradient_color else None
    finder_rgb = _hex_to_rgb(finder_color) if finder_color else fill_rgb

    # Quiet zone override
    if quiet_zone_color and not _is_transparent(quiet_zone_color):
        qz_rgb = _hex_to_rgb(quiet_zone_color) + (255,)
        draw.rectangle([0, 0, total_px, total_px], fill=qz_rgb)
        inner_size = size * box_size
        draw.rectangle([offset, offset, offset + inner_size, offset + inner_size], fill=bg_color)

    def get_color(r: int, c: int) -> tuple:
        if _is_finder(r, c, size):
            return finder_rgb + (255,)
        if grad_rgb:
            if gradient_dir == "horizontal":
                t = c / (size - 1) if size > 1 else 0.0
            elif gradient_dir == "vertical":
                t = r / (size - 1) if size > 1 else 0.0
            elif gradient_dir == "radial":
                cr, cc = size / 2, size / 2
                dist = math.sqrt((r - cr)**2 + (c - cc)**2)
                max_d = math.sqrt(cr**2 + cc**2)
                t = dist / max_d if max_d else 0.0
            else:  # diagonal
                t = (r + c) / (2 * (size - 1)) if size > 1 else 0.0
            return _lerp_color(fill_rgb, grad_rgb, min(t, 1.0)) + (255,)
        return fill_rgb + (255,)

    for r in range(size):
        for c in range(size):
            if not matrix[r][c]:
                continue

            color = get_color(r, c)
            x1 = offset + c * box_size
            y1 = offset + r * box_size
            x2 = x1 + box_size - 1
            y2 = y1 + box_size - 1

            # Finders & separators always render as clean squares
            is_f = _is_finder(r, c, size)
            shape = "square" if is_f else module_shape

            if shape == "circle":
                draw.ellipse([x1, y1, x2, y2], fill=color)

            elif shape == "rounded":
                radius = max(1, box_size // 3)
                draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=color)

            elif shape == "diamond":
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                draw.polygon([(cx, y1), (x2, cy), (cx, y2), (x1, cy)], fill=color)

            elif shape == "gapped":
                gap = max(1, int(box_size * module_gap))
                draw.rectangle([x1 + gap, y1 + gap, x2 - gap, y2 - gap], fill=color)

            elif shape == "star":
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                outer = (box_size - 2) / 2
                inner = outer * 0.4
                pts = []
                for i in range(10):
                    angle = math.pi * i / 5 - math.pi / 2
                    rv = outer if i % 2 == 0 else inner
                    pts.append((cx + rv * math.cos(angle), cy + rv * math.sin(angle)))
                draw.polygon(pts, fill=color)

            elif shape == "vertical_bar":
                gap = int(box_size * 0.2)
                draw.rectangle([x1 + gap, y1, x2 - gap, y2], fill=color)

            elif shape == "horizontal_bar":
                gap = int(box_size * 0.2)
                draw.rectangle([x1, y1 + gap, x2, y2 - gap], fill=color)

            else:  # square
                draw.rectangle([x1, y1, x2 + 1, y2 + 1], fill=color)

    # Logo
    if logo_path:
        try:
            logo = Image.open(logo_path).convert("RGBA")
            logo_ratio = _logo_ratio_limit(
                logo_ratio,
                ecc_level=ecc_level,
                version=version,
                matrix_size=size,
            )
            logo_px = int(total_px * logo_ratio)
            logo = logo.resize((logo_px, logo_px), Image.LANCZOS)
            lx = (total_px - logo_px) // 2
            ly = (total_px - logo_px) // 2
            pad = max(4, box_size // 2)
            draw.rounded_rectangle(
                [lx - pad, ly - pad, lx + logo_px + pad, ly + logo_px + pad],
                radius=pad, fill=(255, 255, 255, 230)
            )
            img.paste(logo, (lx, ly), logo)
        except Exception:
            pass

    if not is_rgba:
        img = img.convert("RGB")

    buf = io.BytesIO()
    fmt = format.upper()
    if fmt in ("JPG", "JPEG"):
        img.convert("RGB").save(buf, format="JPEG", quality=95)
    else:
        img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf
