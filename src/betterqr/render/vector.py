"""
SVG vector renderer for BetterQR.
Finder patterns always rendered as squares for scannability.
"""
from __future__ import annotations
import io
import math
import base64

from ..extras.image_ops import _logo_ratio_limit


def _is_finder(r: int, c: int, size: int, qr_type: str = "standard") -> bool:
    if r < 7 and c < 7:
        return True
    if qr_type != "standard":
        # Micro QR and rMQR have a single finder pattern, top-left only.
        return False
    if r < 7 and c >= size - 7: return True
    if r >= size - 7 and c < 7: return True
    return False


def _svg_color(color: str) -> str:
    return 'none' if color.strip().lower() == 'transparent' else color


def render_svg(
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
    qr_type: str = "standard",
) -> io.BytesIO:
    size = len(matrix)
    total_px = (size + 2 * border) * box_size
    offset = border * box_size
    bs = box_size

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {total_px} {total_px}" '
        f'width="{total_px}" height="{total_px}" '
        f'shape-rendering="crispEdges">\n'
    )

    # Defs
    has_gradient = gradient_color is not None
    if has_gradient:
        parts.append('<defs>\n')
        if gradient_dir == 'radial':
            parts.append(
                f'<radialGradient id="g" cx="50%" cy="50%" r="70%">'
                f'<stop offset="0%" stop-color="{fill_color}"/>'
                f'<stop offset="100%" stop-color="{gradient_color}"/>'
                f'</radialGradient>\n'
            )
        else:
            x1, y1, x2, y2 = {
                'horizontal': ('0%','0%','100%','0%'),
                'vertical':   ('0%','0%','0%','100%'),
                'diagonal':   ('0%','0%','100%','100%'),
            }.get(gradient_dir, ('0%','0%','100%','100%'))
            parts.append(
                f'<linearGradient id="g" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">'
                f'<stop offset="0%" stop-color="{fill_color}"/>'
                f'<stop offset="100%" stop-color="{gradient_color}"/>'
                f'</linearGradient>\n'
            )
        parts.append('</defs>\n')

    module_fill = 'url(#g)' if has_gradient else _svg_color(fill_color)
    finder_fill = _svg_color(finder_color) if finder_color else module_fill

    # Background
    bg = _svg_color(back_color)
    if bg != 'none':
        parts.append(f'<rect width="{total_px}" height="{total_px}" fill="{bg}"/>\n')

    if quiet_zone_color:
        qz = _svg_color(quiet_zone_color)
        inner = size * bs
        parts.append(f'<rect x="0" y="0" width="{total_px}" height="{offset}" fill="{qz}"/>\n')
        parts.append(f'<rect x="0" y="{offset+inner}" width="{total_px}" height="{offset}" fill="{qz}"/>\n')
        parts.append(f'<rect x="0" y="{offset}" width="{offset}" height="{inner}" fill="{qz}"/>\n')
        parts.append(f'<rect x="{offset+inner}" y="{offset}" width="{offset}" height="{inner}" fill="{qz}"/>\n')

    # Optimized rendering: merge all into one <path> for square and gapped modules
    if (module_shape == "square" or module_shape == "gapped") and not finder_color and not has_gradient:
        d = []
        gap_px = bs * module_gap if module_shape == "gapped" else 0
        module_width = bs - 2 * gap_px

        if gap_px == 0:
            # Square, no gap: x/y/module_width are always whole pixels —
            # integer formatting avoids the ~2x cost of float formatting
            # (":.2f") on every single module in the path data.
            mw = int(module_width)
            for r in range(size):
                row_offset = offset + r * bs
                for c in range(size):
                    if matrix[r][c]:
                        x = offset + c * bs
                        d.append(f'M{x},{row_offset}h{mw}v{mw}h-{mw}z')
        else:
            for r in range(size):
                for c in range(size):
                    if matrix[r][c]:
                        x = offset + c * bs + gap_px
                        y = offset + r * bs + gap_px
                        d.append(f'M{x:.2f},{y:.2f}h{module_width:.2f}v{module_width:.2f}h-{module_width:.2f}z')
        if d:
            parts.append(f'<path fill="{module_fill}" d="{" ".join(d)}"/>\n')
    else:
        for r in range(size):
            for c in range(size):
                if not matrix[r][c]:
                    continue
                x = offset + c * bs
                y = offset + r * bs
                is_f = _is_finder(r, c, size, qr_type)
                color = finder_fill if is_f else module_fill
                # Finders always square
                shape = "square" if is_f else module_shape

                if shape == "circle":
                    cx, cy, rad = x + bs/2, y + bs/2, bs/2
                    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{rad}" fill="{color}"/>\n')
                elif shape == "rounded":
                    rad = bs / 3
                    parts.append(f'<rect x="{x}" y="{y}" width="{bs}" height="{bs}" rx="{rad}" ry="{rad}" fill="{color}"/>\n')
                elif shape == "diamond":
                    cx, cy = x + bs/2, y + bs/2
                    parts.append(f'<polygon points="{cx},{y} {x+bs},{cy} {cx},{y+bs} {x},{cy}" fill="{color}"/>\n')
                elif shape == "gapped":
                    gap = bs * module_gap
                    gw = bs - 2*gap
                    parts.append(f'<rect x="{x+gap:.2f}" y="{y+gap:.2f}" width="{gw:.2f}" height="{gw:.2f}" fill="{color}"/>\n')
                elif shape == "star":
                    cx, cy = x + bs/2, y + bs/2
                    outer = bs/2 - 0.5
                    inner = outer * 0.4
                    pts = []
                    for i in range(10):
                        ang = math.pi * i / 5 - math.pi / 2
                        rv = outer if i % 2 == 0 else inner
                        pts.append(f"{cx+rv*math.cos(ang):.2f},{cy+rv*math.sin(ang):.2f}")
                    parts.append(f'<polygon points="{" ".join(pts)}" fill="{color}"/>\n')
                elif shape == "vertical_bar":
                    gap = bs * 0.2
                    parts.append(f'<rect x="{x+gap:.2f}" y="{y}" width="{bs-2*gap:.2f}" height="{bs}" fill="{color}"/>\n')
                elif shape == "horizontal_bar":
                    gap = bs * 0.2
                    parts.append(f'<rect x="{x}" y="{y+gap:.2f}" width="{bs}" height="{bs-2*gap:.2f}" fill="{color}"/>\n')
                else:  # square
                    parts.append(f'<rect x="{x}" y="{y}" width="{bs}" height="{bs}" fill="{color}"/>\n')

    if logo_path:
        try:
            with open(logo_path, 'rb') as f:
                logo_data = f.read()
            b64 = base64.b64encode(logo_data).decode()
            mime = 'image/svg+xml' if logo_path.lower().endswith('.svg') else \
                   'image/jpeg' if logo_path.lower().endswith(('.jpg','.jpeg')) else 'image/png'
            logo_ratio = _logo_ratio_limit(
                logo_ratio,
                ecc_level=ecc_level,
                version=version,
                matrix_size=size,
            )
            logo_px = int(total_px * logo_ratio)
            lx = (total_px - logo_px) // 2
            ly = (total_px - logo_px) // 2
            pad = max(4, bs // 2)
            parts.append(
                f'<rect x="{lx-pad}" y="{ly-pad}" width="{logo_px+2*pad}" height="{logo_px+2*pad}" '
                f'fill="white" rx="{pad}" ry="{pad}"/>\n'
            )
            parts.append(
                f'<image href="data:{mime};base64,{b64}" '
                f'x="{lx}" y="{ly}" width="{logo_px}" height="{logo_px}"/>\n'
            )
        except Exception:
            pass

    parts.append('</svg>\n')
    buf = io.BytesIO()
    buf.write(''.join(parts).encode('utf-8'))
    buf.seek(0)
    return buf


def _hex_to_ps_rgb(color: str) -> str:
    """Convert a '#RRGGBB' (or 3-digit) hex color to a PostScript 'r g b' triplet."""
    c = color.strip().lstrip('#')
    if c.lower() == 'transparent':
        return "1 1 1"  # EPS has no alpha channel; fall back to white.
    if len(c) == 3:
        c = ''.join(ch * 2 for ch in c)
    try:
        r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    except (ValueError, IndexError):
        r, g, b = 0, 0, 0
    return f"{r/255:.4f} {g/255:.4f} {b/255:.4f}"


def render_eps(
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
    qr_type: str = "standard",
) -> io.BytesIO:
    """
    Render the QR matrix as an EPS (Encapsulated PostScript) vector file.

    Note: gradients are not representable in this simple EPS output (the
    solid `fill_color` is used instead), and logo images are not embedded
    (the reserved logo area is left as blank background, matching what
    the underlying matrix already encodes) — use SVG or PNG/PDF if you
    need either of those.
    """
    size = len(matrix)
    total_px = (size + 2 * border) * box_size
    offset = border * box_size
    bs = box_size

    ops: list[str] = []

    def rect(x, y, w, h):
        ops.append(f"newpath {x:.2f} {y:.2f} moveto {w:.2f} 0 rlineto "
                    f"0 {h:.2f} rlineto {-w:.2f} 0 rlineto closepath fill")

    def circle(cx, cy, r):
        ops.append(f"newpath {cx:.2f} {cy:.2f} {r:.2f} 0 360 arc closepath fill")

    def rounded_rect(x, y, w, h, r):
        ops.append(
            f"newpath {x+r:.2f} {y:.2f} moveto "
            f"{x+w-r:.2f} {y:.2f} lineto {x+w:.2f} {y:.2f} {x+w:.2f} {y+r:.2f} {r:.2f} arcto 4 {{pop}} repeat "
            f"{x+w:.2f} {y+h-r:.2f} lineto {x+w:.2f} {y+h:.2f} {x+w-r:.2f} {y+h:.2f} {r:.2f} arcto 4 {{pop}} repeat "
            f"{x+r:.2f} {y+h:.2f} lineto {x:.2f} {y+h:.2f} {x:.2f} {y+h-r:.2f} {r:.2f} arcto 4 {{pop}} repeat "
            f"{x:.2f} {y+r:.2f} lineto {x:.2f} {y:.2f} {x+r:.2f} {y:.2f} {r:.2f} arcto 4 {{pop}} repeat "
            f"closepath fill"
        )

    def polygon(points):
        pts = " ".join(f"{px:.2f} {py:.2f}" for px, py in points)
        first = f"{points[0][0]:.2f} {points[0][1]:.2f}"
        rest = " lineto ".join(f"{px:.2f} {py:.2f}" for px, py in points[1:])
        ops.append(f"newpath {first} moveto {rest} lineto closepath fill")

    def set_color(hexval):
        ops.append(f"{_hex_to_ps_rgb(hexval)} setrgbcolor")

    # Background
    set_color(back_color)
    rect(0, 0, total_px, total_px)

    if quiet_zone_color:
        set_color(quiet_zone_color)
        inner = size * bs
        rect(0, 0, total_px, offset)                        # top band
        rect(0, total_px - offset, total_px, offset)         # bottom band
        rect(0, offset, offset, inner)                       # left band
        rect(total_px - offset, offset, offset, inner)       # right band

    module_fill = fill_color
    finder_fill = finder_color if finder_color else module_fill
    last_color = None

    for r in range(size):
        for c in range(size):
            if not matrix[r][c]:
                continue
            x = offset + c * bs
            y = offset + r * bs
            is_f = _is_finder(r, c, size, qr_type)
            color = finder_fill if is_f else module_fill
            shape = "square" if is_f else module_shape

            if color != last_color:
                set_color(color)
                last_color = color

            if shape == "circle":
                circle(x + bs / 2, y + bs / 2, bs / 2)
            elif shape == "rounded":
                rounded_rect(x, y, bs, bs, bs / 3)
            elif shape == "diamond":
                cx, cy = x + bs / 2, y + bs / 2
                polygon([(cx, y), (x + bs, cy), (cx, y + bs), (x, cy)])
            elif shape == "gapped":
                gap = bs * module_gap
                rect(x + gap, y + gap, bs - 2 * gap, bs - 2 * gap)
            elif shape == "star":
                cx, cy = x + bs / 2, y + bs / 2
                outer = bs / 2 - 0.5
                inner = outer * 0.4
                pts = []
                for i in range(10):
                    ang = math.pi * i / 5 - math.pi / 2
                    rv = outer if i % 2 == 0 else inner
                    pts.append((cx + rv * math.cos(ang), cy + rv * math.sin(ang)))
                polygon(pts)
            elif shape == "vertical_bar":
                gap = bs * 0.2
                rect(x + gap, y, bs - 2 * gap, bs)
            elif shape == "horizontal_bar":
                gap = bs * 0.2
                rect(x, y + gap, bs, bs - 2 * gap)
            else:  # square
                rect(x, y, bs, bs)

    header = (
        "%!PS-Adobe-3.0 EPSF-3.0\n"
        f"%%BoundingBox: 0 0 {total_px} {total_px}\n"
        f"%%HiResBoundingBox: 0 0 {total_px} {total_px}\n"
        "%%Pages: 1\n"
        "%%EndComments\n"
        "%%Page: 1 1\n"
        # Flip Y so (0,0) is the top-left, matching the SVG renderer's
        # coordinate system, instead of PostScript's native bottom-left origin.
        f"0 {total_px} translate 1 -1 scale\n"
    )
    footer = "\nshowpage\n%%EOF\n"

    eps_text = header + "\n".join(ops) + footer
    buf = io.BytesIO()
    buf.write(eps_text.encode("utf-8"))
    buf.seek(0)
    return buf
