"""
Animated QR Code renderer for BetterQR.
Generates animated GIF or APNG from a QR code with various animations:
  - fade      : modules fade in/out
  - scan      : scanline sweeps across
  - pulse     : finder patterns pulse
  - matrix    : Matrix-style rain effect
  - build     : modules build in row by row
  - shimmer   : gradient shimmer sweeps across
  - rotate    : color rotates around hue wheel
  - wave      : sine-wave ripple across modules
"""
from __future__ import annotations
import io
import math
import random
from typing import Callable


def _hex_to_rgb(c: str) -> tuple[int,int,int]:
    c = c.strip().lstrip('#')
    if len(c) == 3: c = ''.join(x*2 for x in c)
    return int(c[0:2],16), int(c[2:4],16), int(c[4:6],16)


def _lerp(a, b, t):
    return a + (b - a) * t


def _lerp_rgb(c1, c2, t):
    return tuple(int(_lerp(c1[i], c2[i], t)) for i in range(3))


def _is_finder(r, c, size):
    if r < 7 and c < 7: return True
    if r < 7 and c >= size-7: return True
    if r >= size-7 and c < 7: return True
    return False


def _draw_module(draw, x1, y1, x2, y2, color, shape, box_size):
    """Draw a single module with the given shape."""
    try:
        from PIL import ImageDraw
    except ImportError:
        pass

    if shape == "circle":
        draw.ellipse([x1, y1, x2-1, y2-1], fill=color)
    elif shape == "rounded":
        r = max(1, box_size // 3)
        draw.rounded_rectangle([x1, y1, x2-1, y2-1], radius=r, fill=color)
    elif shape == "diamond":
        cx, cy = (x1+x2)//2, (y1+y2)//2
        draw.polygon([(cx,y1),(x2-1,cy),(cx,y2-1),(x1,cy)], fill=color)
    else:
        draw.rectangle([x1, y1, x2, y2], fill=color)


def _make_base_frame(
    matrix, box_size, border,
    fill_rgb, back_rgb,
    module_shape, finder_rgb,
    highlight_mask=None,
):
    """Render one frame. highlight_mask controls per-module brightness multiplier."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        raise ImportError("Pillow required: pip install Pillow")

    size = len(matrix)
    total = (size + 2*border) * box_size
    offset = border * box_size

    img = Image.new("RGB", (total, total), back_rgb)
    draw = ImageDraw.Draw(img)

    for r in range(size):
        for c in range(size):
            if not matrix[r][c]:
                continue

            t = highlight_mask[r][c] if highlight_mask is not None else 1.0
            is_f = _is_finder(r, c, size)
            base_color = finder_rgb if is_f else fill_rgb

            color = _lerp_rgb(back_rgb, base_color, max(0.0, min(1.0, t)))

            x1 = offset + c*box_size
            y1 = offset + r*box_size
            x2 = x1 + box_size
            y2 = y1 + box_size

            _draw_module(draw, x1, y1, x2, y2, color,
                         "square" if is_f else module_shape, box_size)
    return img


def animate(
    matrix: list[list[int]],
    effect: str = "shimmer",
    n_frames: int = 20,
    fps: int = 15,
    box_size: int = 10,
    border: int = 4,
    fill_color: str = "#000000",
    back_color: str = "#FFFFFF",
    module_shape: str = "square",
    finder_color: str | None = None,
    accent_color: str | None = None,
    loop: int = 0,
) -> io.BytesIO:
    """
    Generate an animated GIF of the QR code.

    Effects:
        shimmer   - light sweep across
        fade      - fade in from background
        scan      - scanline sweeps top-to-bottom
        pulse     - finder patterns throb
        build     - modules reveal row by row
        matrix    - random reveal with trails
        wave      - sine wave ripple
        rotate    - hue-rotate color (needs accent_color)
        blink     - entire QR blinks on/off
        typewriter- modules appear left-to-right top-to-bottom

    Args:
        matrix:       QR code matrix (from QR.matrix)
        effect:       Animation effect name
        n_frames:     Number of frames
        fps:          Frames per second
        box_size:     Pixels per module
        border:       Quiet zone in modules
        fill_color:   Dark module color
        back_color:   Background color
        module_shape: Module shape
        finder_color: Finder pattern color
        accent_color: Secondary color for some effects
        loop:         GIF loop count (0 = infinite)

    Returns:
        BytesIO containing the animated GIF
    """
    try:
        from PIL import Image
    except ImportError:
        raise ImportError("Pillow required: pip install Pillow")

    fill_rgb = _hex_to_rgb(fill_color)
    back_rgb = _hex_to_rgb(back_color)
    finder_rgb = _hex_to_rgb(finder_color) if finder_color else fill_rgb
    accent_rgb = _hex_to_rgb(accent_color) if accent_color else fill_rgb

    size = len(matrix)
    frames: list[Image.Image] = []

    def masks_shimmer():
        for f in range(n_frames):
            band_center = (f / n_frames) * (size + 4) - 2
            mask = []
            for r in range(size):
                row = []
                for c in range(size):
                    dist = abs(c - band_center)
                    t = max(0.0, 1.0 - dist / 3.0)
                    row.append((0.55 + t * 0.45) if matrix[r][c] else 0.0)
                mask.append(row)
            yield mask

    def masks_fade():
        for f in range(n_frames):
            t = f / (n_frames - 1)
            t = t * t * (3 - 2 * t)
            mask = [[t if matrix[r][c] else 0.0 for c in range(size)] for r in range(size)]
            yield mask

    def masks_scan():
        for f in range(n_frames):
            scan_row = f / max(n_frames - 1, 1) * (size + 2)
            mask = []
            for r in range(size):
                if r < scan_row - 2:
                    row = [1.0 if matrix[r][c] else 0.0 for c in range(size)]
                elif r < scan_row:
                    t = 1.0 - (scan_row - r) / 2
                    row = [t if matrix[r][c] else 0.0 for c in range(size)]
                else:
                    row = [0.0] * size
                mask.append(row)
            yield mask

    def masks_pulse():
        for f in range(n_frames):
            t = (math.sin(2 * math.pi * f / n_frames) + 1) / 2
            mask = []
            for r in range(size):
                row = []
                for c in range(size):
                    if not matrix[r][c]:
                        row.append(0.0)
                    elif _is_finder(r, c, size):
                        row.append(0.5 + t * 0.5)
                    else:
                        row.append(1.0)
                mask.append(row)
            yield mask

    def masks_build():
        for f in range(n_frames):
            progress = f / max(n_frames - 1, 1)
            rows_visible = int(progress * (size + 1))
            mask = []
            for r in range(size):
                if r < rows_visible:
                    row = [1.0 if matrix[r][c] else 0.0 for c in range(size)]
                elif r == rows_visible:
                    partial = progress * (size + 1) - rows_visible
                    row = [partial if matrix[r][c] else 0.0 for c in range(size)]
                else:
                    row = [0.0] * size
                mask.append(row)
            yield mask

    def masks_matrix():
        drops = [random.random() * size for _ in range(size)]
        settled = [False] * size
        for f in range(n_frames):
            progress = f / max(n_frames - 1, 1)
            for c in range(size):
                drops[c] = (drops[c] + random.uniform(0.5, 1.5)) % (size + 5)
                # Columns increasingly settle (lock to full brightness) as animation nears end
                if not settled[c] and progress > 0.6:
                    if random.random() < (progress - 0.6) / 0.4 * 0.3:
                        settled[c] = True
            mask = []
            for r in range(size):
                row = []
                for c in range(size):
                    if not matrix[r][c]:
                        row.append(0.0)
                        continue
                    # Last frame: everything fully visible so the code can be scanned
                    if f == n_frames - 1:
                        row.append(1.0)
                        continue
                    if settled[c]:
                        row.append(1.0)
                        continue
                    drop = drops[c] % size
                    dist = (drop - r) % size
                    if dist < 3:
                        row.append(1.0 - dist * 0.25)
                    elif r < drop:
                        row.append(0.4)
                    else:
                        row.append(0.0)
                mask.append(row)
            yield mask

    def masks_wave():
        for f in range(n_frames):
            phase = 2 * math.pi * f / n_frames
            mask = []
            for r in range(size):
                row = []
                for c in range(size):
                    if not matrix[r][c]:
                        row.append(0.0)
                        continue
                    wave = (math.sin(phase + (r + c) * 0.4) + 1) / 2
                    row.append(0.5 + wave * 0.5)
                mask.append(row)
            yield mask

    def masks_blink():
        for f in range(n_frames):
            t = (math.sin(2 * math.pi * f / n_frames * 2) + 1) / 2
            mask = [[t if matrix[r][c] else 0.0 for c in range(size)] for r in range(size)]
            yield mask

    def masks_typewriter():
        all_modules = [(r, c) for r in range(size) for c in range(size) if matrix[r][c]]
        total = len(all_modules)
        revealed = set()
        for f in range(n_frames):
            count = int(f / (n_frames - 1) * total)
            for i in range(len(revealed), min(count, total)):
                revealed.add(all_modules[i])
            mask = []
            for r in range(size):
                row = []
                for c in range(size):
                    row.append(1.0 if (r, c) in revealed and matrix[r][c] else 0.0)
                mask.append(row)
            yield mask

    generators = {
        "shimmer":    masks_shimmer,
        "fade":       masks_fade,
        "scan":       masks_scan,
        "pulse":      masks_pulse,
        "build":      masks_build,
        "matrix":     masks_matrix,
        "wave":       masks_wave,
        "blink":      masks_blink,
        "typewriter": masks_typewriter,
    }

    gen_fn = generators.get(effect, masks_shimmer)

    def get_frame_colors(f):
        """For 'rotate' effect, shift hue each frame."""
        if effect == "rotate":
            hue_shift = (f / n_frames) * 360
            import colorsys
            # Use accent_rgb as the color to rotate; if it's too dark/desaturated,
            # fall back to a vivid reference so the effect is visible.
            base = accent_rgb if accent_color else fill_rgb
            r_, g_, b_ = [x / 255 for x in base]
            h, s, v = colorsys.rgb_to_hsv(r_, g_, b_)
            if s < 0.2 or v < 0.2:
                # Boost to a vivid color so hue rotation is perceptible
                s, v = 0.85, 0.85
            h = (h + hue_shift / 360) % 1.0
            nr, ng, nb = colorsys.hsv_to_rgb(h, s, v)
            return (int(nr * 255), int(ng * 255), int(nb * 255)), finder_rgb
        return fill_rgb, finder_rgb

    if effect == "rotate":
        for f in range(n_frames):
            fr, finder_r = get_frame_colors(f)
            mask = [[1.0 if matrix[r][c] else 0.0 for c in range(size)] for r in range(size)]
            img = _make_base_frame(matrix, box_size, border, fr, back_rgb,
                                   module_shape, finder_r, mask)
            frames.append(img)
    else:
        for mask in gen_fn():
            img = _make_base_frame(matrix, box_size, border, fill_rgb, back_rgb,
                                   module_shape, finder_rgb, mask)
            frames.append(img)

    # ---------- Encode GIF ----------
    duration_ms = int(1000 / fps)
    buf = io.BytesIO()

    # Convert to palette mode for smaller GIFs
    palette_frames = [f.quantize(colors=64, method=Image.Quantize.FASTOCTREE) for f in frames]

    palette_frames[0].save(
        buf,
        format="GIF",
        save_all=True,
        append_images=palette_frames[1:],
        loop=loop,
        duration=duration_ms,
        optimize=True,
    )
    buf.seek(0)
    return buf
