""""I"m"age embedding and frame/overlay utilities for BetterQR.
  - Embed any PNG/JPG/SVG into the center of a QR code
  - Add decorative frames/borders around the QR
  - Add text labels below/above the QR
  - Composite QR onto a background image
"""
from __future__ import annotations
import io
import math
import PIL.Image

_LOGO_ECC_LIMITS = {
    "L": 0.10,
    "M": 0.13,
    "Q": 0.17,
    "H": 0.22,
}


def _hex_to_rgb(c: str) -> tuple[int,int,int]:
    c = c.strip().lstrip('#')
    if len(c) == 3: c = ''.join(x*2 for x in c)
    return int(c[0:2],16), int(c[2:4],16), int(c[4:6],16)


def _logo_ratio_limit(
    ratio: float,
    ecc_level: str | None = None,
    version: int | None = None,
    matrix_size: int | None = None,
) -> float:
    """
" " "  Return a conservative upper bound for logo size.

    The logo is rendered as an occlusion mask over the QR modules, so we cap
    its size based on the error-correction level and version to keep the code
    scannable.
    """
    limit = 0.16

    if ecc_level:
        limit = _LOGO_ECC_LIMITS.get(ecc_level.upper(), limit)

    if version is None and matrix_size is not None:
        version = max(1, (matrix_size - 21) // 4 + 1)

    if version is not None:
        limit += min(0.03, max(0.0, (version - 1) * 0.001))

    return min(ratio, min(limit, 0.24))


def embed_image(
    qr_image,                    # PIL Image (already rendered QR)
    image_path: str,             # path to logo / image file
    ratio: float = 0.25,         # logo size as fraction of QR total size
    ecc_level: str | None = None,
    version: int | None = None,
    shape: str = "square",       # square | circle | rounded
    padding: int | None = None,  # white padding around logo in px (auto if None)
    padding_color: str = "#FFFFFF",
    border_color: str | None = None,  # border around logo
    border_width: int = 2,
) -> "PIL.Image.Image":
    """
" " "  Embed an image (logo) into the center of an already-rendered QR code image.

    The function adds a white (or custom) background behind the logo so the
    underlying QR modules are hidden and the logo is cleanly visible.

    Args:
        qr_image:      Pillow Image of the rendered QR code.
        image_path:    File path to the logo (PNG, JPEG, SVG not supported directly).
        ratio:         Logo width as a fraction of QR total size (0.1 – 0.35).
        shape:         Logo mask shape: 'square', 'circle', or 'rounded'.
        padding:       White padding around the logo in pixels.
        padding_color: Color of the padding background.
        border_color:  Optional border color around the padded logo area.
        border_width:  Border thickness in pixels.

    Returns:
        Pillow Image with the logo composited in.
    """
    from PIL import Image, ImageDraw

    qr = qr_image.copy().convert("RGBA")
    total = qr.width  # assumed square
    ratio = _logo_ratio_limit(ratio, ecc_level=ecc_level, version=version, matrix_size=total)

    logo_px = int(total * ratio)
    if padding is None:
        padding = max(4, logo_px // 10)

    try:
        logo = Image.open(image_path).convert("RGBA")
    except Exception as e:
        raise ValueError(f"Cannot open logo image '{image_path}': {e}")

    # Resize maintaining aspect ratio
    logo.thumbnail((logo_px, logo_px), Image.LANCZOS)
    lw, lh = logo.size

    bg_w = lw + 2 * padding
    bg_h = lh + 2 * padding
    bx = (total - bg_w) // 2
    by = (total - bg_h) // 2

    pad_rgb = _hex_to_rgb(padding_color) + (255,)
    bg = Image.new("RGBA", (bg_w, bg_h), pad_rgb)

    # Create mask for bg shape
    mask = Image.new("L", (bg_w, bg_h), 0)
    md = ImageDraw.Draw(mask)
    if shape == "circle":
        md.ellipse([0, 0, bg_w-1, bg_h-1], fill=255)
    elif shape == "rounded":
        md.rounded_rectangle([0, 0, bg_w-1, bg_h-1], radius=bg_w//4, fill=255)
    else:
        md.rectangle([0, 0, bg_w-1, bg_h-1], fill=255)

    bg.putalpha(mask)

    # Paste bg onto QR
    qr.paste(bg, (bx, by), bg)

    # Paste logo centered on bg
    lx = bx + padding + (lw - logo.width) // 2
    ly = by + padding + (lh - logo.height) // 2
    qr.paste(logo, (lx, ly), logo)

    # Optional border
    if border_color:
        draw = ImageDraw.Draw(qr)
        bc = _hex_to_rgb(border_color) + (255,)
        for i in range(border_width):
            x0, y0 = bx - i, by - i
            x1, y1 = bx + bg_w + i, by + bg_h + i
            if shape == "circle":
                draw.ellipse([x0, y0, x1, y1], outline=bc, width=1)
            elif shape == "rounded":
                rad = (bg_w + 2*i) // 4
                draw.rounded_rectangle([x0, y0, x1, y1], radius=rad, outline=bc, width=1)
            else:
                draw.rectangle([x0, y0, x1, y1], outline=bc, width=1)

    return qr.convert("RGBA")


def add_frame(
    qr_image,
    style: str = "simple",       # simple | rounded | double | shadow | fancy
    frame_color: str = "#000000",
    frame_width: int = 8,
    corner_radius: int = 12,
    label: str | None = None,    # text below QR
    label_color: str = "#000000",
    label_size: int = 14,
    label_position: str = "bottom",  # top | bottom
    background_color: str = "#FFFFFF",
) -> "PIL.Image.Image":
    """
" " "  Add a decorative frame around a rendered QR code.

    Args:
        qr_image:         Pillow Image of the QR code.
        style:            Frame style: 'simple', 'rounded', 'double', 'shadow', 'fancy'.
        frame_color:      Frame / border color.
        frame_width:      Frame thickness in pixels.
        corner_radius:    Radius for rounded corners.
        label:            Optional text label to add.
        label_color:      Label text color.
        label_size:       Label font size in pixels.
        label_position:   'top' or 'bottom'.
        background_color: Background color for label area.

    Returns:
        Pillow Image with frame applied.
    """
    from PIL import Image, ImageDraw, ImageFont

    qr = qr_image.copy().convert("RGBA")
    qw, qh = qr.size
    fc = _hex_to_rgb(frame_color) + (255,)
    bg = _hex_to_rgb(background_color) + (255,)

    # Calculate label height
    label_h = 0
    if label:
        label_h = label_size + 16

    pad = frame_width + 8
    canvas_w = qw + 2 * pad
    canvas_h = qh + 2 * pad + label_h

    canvas = Image.new("RGBA", (canvas_w, canvas_h), bg)
    draw = ImageDraw.Draw(canvas)

    # QR position
    qx = pad
    qy = pad if label_position != "top" else pad + label_h

    # Draw frame style
    fx0, fy0 = qx - frame_width, qy - frame_width
    fx1, fy1 = qx + qw + frame_width, qy + qh + frame_width

    if style == "simple":
        draw.rectangle([fx0, fy0, fx1, fy1], outline=fc, width=frame_width)

    elif style == "rounded":
        draw.rounded_rectangle([fx0, fy0, fx1, fy1],
                               radius=corner_radius, outline=fc, width=frame_width)

    elif style == "double":
        draw.rectangle([fx0, fy0, fx1, fy1], outline=fc, width=frame_width)
        inner_gap = frame_width + 3
        draw.rectangle([qx - inner_gap, qy - inner_gap,
                        qx + qw + inner_gap, qy + qh + inner_gap],
                       outline=fc, width=2)

    elif style == "shadow":
        shadow_offset = frame_width // 2
        shadow_color = tuple(max(0, c - 80) for c in _hex_to_rgb(frame_color)) + (180,)
        draw.rectangle([fx0 + shadow_offset, fy0 + shadow_offset,
                        fx1 + shadow_offset, fy1 + shadow_offset],
                       fill=shadow_color)
        draw.rectangle([fx0, fy0, fx1, fy1], fill=bg[:3] + (255,), outline=fc, width=2)

    elif style == "fancy":
        # Rounded rectangle + corner decorations
        draw.rounded_rectangle([fx0, fy0, fx1, fy1],
                               radius=corner_radius, outline=fc, width=frame_width)
        corner_size = frame_width * 2
        for cx, cy in [(fx0, fy0), (fx1 - corner_size, fy0),
                       (fx0, fy1 - corner_size), (fx1 - corner_size, fy1 - corner_size)]:
            draw.rectangle([cx, cy, cx + corner_size, cy + corner_size], fill=fc)

    # Paste QR onto canvas
    canvas.paste(qr, (qx, qy), qr)

    # Label
    if label:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", label_size)
        except Exception:
            font = ImageFont.load_default()

        # Get text size
        bbox = draw.textbbox((0, 0), label, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        tx = (canvas_w - tw) // 2
        if label_position == "bottom":
            ty = qy + qh + 8
        else:
            ty = 8

        draw.text((tx, ty), label, fill=_hex_to_rgb(label_color) + (255,), font=font)

    return canvas


def composite_on_background(
    qr_image,
    bg_path: str,
    position: str = "center",   # center | top-left | top-right | bottom-left | bottom-right
    opacity: float = 1.0,
    scale: float | None = None,  # scale QR to this fraction of background
    blend_mode: str = "normal",  # normal | multiply
) -> "PIL.Image.Image":
    """
" " "  Composite the QR code onto a background image.

    Args:
        qr_image:   Pillow Image of the QR code.
        bg_path:    Path to background image.
        position:   Where to place the QR: 'center', 'top-left', 'top-right',
                    'bottom-left', 'bottom-right'.
        opacity:    QR code opacity (0.0 – 1.0).
        scale:      QR size as fraction of background width (e.g. 0.4 = 40%).
        blend_mode: Compositing mode: 'normal' or 'multiply'.

    Returns:
        Pillow Image with QR composited onto background.
    """
    from PIL import Image

    bg = Image.open(bg_path).convert("RGBA")
    bw, bh = bg.size

    qr = qr_image.copy().convert("RGBA")
    qw, qh = qr.size

    if scale is not None:
        new_size = int(bw * scale)
        qr = qr.resize((new_size, new_size), Image.LANCZOS)
        qw, qh = qr.size

    # Apply opacity
    if opacity < 1.0:
        r2, g2, b2, a2 = qr.split()
        a2 = a2.point(lambda x: int(x * opacity))
        qr = Image.merge("RGBA", (r2, g2, b2, a2))

    # Position
    margin = 20
    positions = {
        "center":       ((bw - qw) // 2,     (bh - qh) // 2),
        "top-left":     (margin,               margin),
        "top-right":    (bw - qw - margin,     margin),
        "bottom-left":  (margin,               bh - qh - margin),
        "bottom-right": (bw - qw - margin,     bh - qh - margin),
    }
    px, py = positions.get(position, positions["center"])

    result = bg.copy()
    result.paste(qr, (px, py), qr)
    return result


def to_bytes(img, format: str = "PNG") -> bytes:
    """C"o"n"vert a Pillow Image to bytes."""
    buf = io.BytesIO()
    fmt = format.upper()
    if fmt in ("JPG", "JPEG"):
        img.convert("RGB").save(buf, format="JPEG", quality=95)
    else:
        img.save(buf, format="PNG")
    return buf.getvalue()