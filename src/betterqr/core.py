"""
BetterQR Core: The primary API for QR code generation.
"""
from __future__ import annotations
import io
from typing import Literal
from .exceptions import LowContrastWarning
from .helpers import (
    wifi_string,
    WiFi,
    VCard,
    MeCard,
    GeoLocation,
    Event,
    SMS,
    Email,
    Phone,
    Crypto,
    batch,
)
from .encoder import encode_data
from .matrix import build_matrix
from .render.vector import render_svg
from .render.raster import render_png as render_raster
from .render.terminal import render_terminal

ECC_LEVELS = ('L', 'M', 'Q', 'H')
SHAPES = ('square', 'circle', 'rounded', 'diamond', 'gapped', 'star', 'vertical_bar', 'horizontal_bar')
FRAME_STYLES = ('simple', 'rounded', 'double', 'shadow', 'fancy')
ANIM_EFFECTS = ('shimmer', 'fade', 'scan', 'pulse', 'build', 'matrix', 'wave', 'blink', 'typewriter', 'rotate')

def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

def _luminance(r: int, g: int, b: int) -> float:
    # Formula for relative luminance (Rec. 709)
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255

def _contrast_ratio(lum1: float, lum2: float) -> float:
    l1 = max(lum1, lum2)
    l2 = min(lum1, lum2)
    return (l1 + 0.05) / (l2 + 0.05)

class QR:
    """
    High-level QR Code object.
    
    Usage:
        qr = QR("https://example.com")
        qr.style(fill_color="#1D4ED8", module_shape="rounded")
        qr.save("my_qr.png")
    """

    def __init__(self, data, ecc: str = 'M', version: int | None = None, qr_type: str = "standard"):
        ecc = ecc.upper()
        if ecc not in ECC_LEVELS:
            raise ValueError(f"ecc must be one of {ECC_LEVELS}")

        # Micro QR ECC validation
        if qr_type == "micro" and ecc not in ('L', 'M', 'Q'):
            raise ValueError("Micro QR only supports ECC levels L, M, Q (not H)")

        self._raw     = str(data)
        self._ecc     = ecc
        self._version_hint = version
        self._qr_type = qr_type

        # Style state
        self._fill         = "#000000"
        self._back         = "#FFFFFF"
        self._shape        = "square"
        self._finder_color = None
        self._gap          = 0.15
        self._quiet_color  = None
        self._box_size     = 10
        self._border       = 4
        self._grad_end     = None
        self._grad_dir     = "diagonal"

        self._logo_path    = None
        self._logo_ratio   = 0.2
        self._logo_shape   = "square"
        self._logo_padding = 2
        self._logo_pad_color = "#FFFFFF"
        self._logo_border  = 0
        self._logo_border_w = 2

        # Frame/Text state
        self._frame_style  = None
        self._frame_color  = None
        self._frame_width  = 0
        self._frame_radius = 0
        self._label        = None
        self._label_color  = "#000000"
        self._label_size   = 14
        self._label_pos    = "bottom"

        # Animation state
        self._anim_effect  = None
        self._anim_frames  = 20
        self._anim_fps     = 15
        self._anim_accent  = None
        self._anim_loop    = 0

        self._rebuild(version=version, qr_type=qr_type)

    def _rebuild(self, ecc: str | None = None, version: int | None = None, qr_type: str | None = None) -> None:
        ecc = (ecc or self._ecc).upper()
        if ecc not in ECC_LEVELS:
            raise ValueError(f"ecc must be one of {ECC_LEVELS}")

        version_hint = self._version_hint if version is None else version
        qr_type = qr_type or self._qr_type

        self._codewords, self._version, self._mode = encode_data(
            self._raw, ecc, version_hint, qr_type=qr_type
        )
        logo_info = self._get_logo_info()
        self._matrix = build_matrix(self._codewords, self._version, ecc, qr_type=qr_type, logo_info=logo_info)
        self._ecc = ecc

    # ──────────────────────────────────────────────────────────────────
    # Styling

    def style(
        self,
        fill_color: str | None = None,
        back_color: str | None = None,
        module_shape: str | None = None,
        finder_color: str | None = None,
        module_gap: float | None = None,
        quiet_zone_color: str | None = None,
        gradient_color: str | None = None,
        gradient_dir: str = "diagonal",
        dark_mode: bool = False,
        auto_fix_contrast: bool = False,
        box_size: int | None = None,
        border: int | None = None,
        fill: str | None = None,
        back: str | None = None,
        shape: str | None = None,
        finder: str | None = None,
    ) -> "QR":
        """
        Set visual style. Returns self for chaining.
        """
        fill = fill_color or fill or self._fill
        back = back_color or back or self._back
        shape = module_shape or shape or self._shape
        finder = finder_color or finder or self._finder_color
        gap = module_gap if module_gap is not None else self._gap
        quiet_color = quiet_zone_color or self._quiet_color

        self._fill  = fill
        self._back  = back
        self._shape = shape
        self._finder_color = finder
        self._gap   = gap
        self._quiet_color = quiet_color
        self._grad_end = gradient_color
        self._grad_dir = gradient_dir
        if box_size is not None: self._box_size = box_size
        if border   is not None: self._border   = border

        if self._shape not in SHAPES:
            raise ValueError(f"shape must be one of {SHAPES}")

        # Dark-Mode Inversion Optimization
        if dark_mode:
            original_fill = self._fill
            original_back = self._back
            self._fill = original_back
            self._back = original_fill
            auto_fix_contrast = True

        # Luminance Guard
        if self._back != "transparent":
            fill_rgb = _hex_to_rgb(self._fill)
            back_rgb = _hex_to_rgb(self._back)

            lum_fill = _luminance(*fill_rgb)
            lum_back = _luminance(*back_rgb)

            contrast = _contrast_ratio(lum_fill, lum_back)

            if contrast < 4.5:
                import warnings
                msg = (f"Low contrast detected (ratio: {contrast:.2f}). "
                       f"Foreground: {self._fill}, Background: {self._back}. "
                       "Consider adjusting colors for better scannability.")
                warnings.warn(msg, LowContrastWarning)

                if auto_fix_contrast:
                    if lum_back > 0.5: # Light background
                        self._fill = "#000000" # make fill black
                    else: # Dark background
                        self._fill = "#FFFFFF" # make fill white
                    warnings.warn(f"Contrast auto-fixed. New foreground: {self._fill}", LowContrastWarning)

        return self

    def gradient(self, start_color: str, end_color: str, direction: str = "diagonal") -> "QR":
        """Apply a gradient fill."""
        self._fill = start_color
        self._grad_end = end_color
        self._grad_dir = direction
        return self

    def colors(self, dark: str, light: str = "#FFFFFF") -> "QR":
        """Quick color setter.  qr.colors('#3B82F6', '#EFF6FF')"""
        self._fill = dark
        self._back = light
        return self

    # ──────────────────────────────────────────────────────────────────
    def logo(
        self,
        path: str,
        ratio: float = 0.2,
        shape: Literal['square', 'circle'] = 'square',
        padding: int = 2,
        padding_color: str = "#FFFFFF",
        border: int = 0,
        border_width: int = 2,
    ) -> "QR":
        """
        Add a logo to the center of the QR code.
        """
        self._logo_path    = path
        self._logo_ratio   = ratio
        self._logo_shape   = shape
        self._logo_padding = padding
        self._logo_pad_color = padding_color
        self._logo_border  = border
        self._logo_border_w = border_width
        if self._ecc != "H":
            self._rebuild(ecc="H")
        return self

    def _get_logo_info(self) -> dict | None:
        if self._logo_path:
            return {
                "logo_path": self._logo_path,
                "ratio": self._logo_ratio,
                "shape": self._logo_shape,
                "padding": self._logo_padding,
                "padding_color": self._logo_pad_color,
                "border": self._logo_border,
                "border_width": self._logo_border_w,
                "box_size": self._box_size,
                "border_modules": self._border
            }
        return None

    def frame(self, style: str, color: str = "#000000", width: int = 40,
              radius: int = 20, label: str | None = None,
              label_color: str = "#000000", label_size: int = 14,
              label_position: str = "bottom") -> "QR":
        """
        Add a decorative frame around the QR code.
        """
        if style not in FRAME_STYLES:
            raise ValueError(f"style must be one of {FRAME_STYLES}")
        self._frame_style  = style
        self._frame_color  = color
        self._frame_width  = width
        self._frame_radius = radius
        self._label        = label
        self._label_color  = label_color
        self._label_size   = label_size
        self._label_pos    = label_position
        return self

    def label(self, text: str, color: str = "#000000", size: int = 14,
              position: str = "bottom") -> "QR":
        """Shortcut: add a text label."""
        if self._frame_style is None:
            self._frame_style = "simple"
            self._frame_width = 0
        self._label       = text
        self._label_color = color
        self._label_size  = size
        self._label_pos   = position
        return self

    # ──────────────────────────────────────────────────────────────────
    # Animation

    def animate(
        self,
        effect: str = "shimmer",
        frames: int = 20,
        fps: int = 15,
        accent: str | None = None,
        loop: int = 0,
    ) -> "QR":
        """
        Make the QR code animated.
        """
        if effect not in ANIM_EFFECTS:
            raise ValueError(f"effect must be one of {ANIM_EFFECTS}")
        self._anim_effect = effect
        self._anim_frames = frames
        self._anim_fps    = fps
        self._anim_accent = accent
        self._anim_loop   = loop
        return self

    # ──────────────────────────────────────────────────────────────────
    # Output Methods

    def _render_static(self, fmt: str, box_size: int, border: int, **overrides) -> io.BytesIO:
        """Render static image, apply logo/frame post-processing."""
        kw = dict(
            box_size      = box_size,
            border        = border,
            fill_color    = self._fill,
            back_color    = self._back,
            module_shape  = self._shape,
            gradient_color= self._grad_end,
            gradient_dir  = self._grad_dir,
            finder_color  = self._finder_color,
            logo_path     = self._logo_path if fmt == "SVG" else None,
            logo_ratio    = self._logo_ratio,
            ecc_level     = self._ecc,
            version       = self._version,
            module_gap    = self._gap,
            quiet_zone_color = self._quiet_color,
        )
        kw.update(overrides)

        if fmt == "SVG":
            return render_svg(self._matrix, **kw)

        buf = render_raster(self._matrix, format=fmt, **kw)

        # Post-process: embed logo (for raster)
        if self._logo_path:
            from .extras.image_ops import embed_image
            from PIL import Image
            img = Image.open(buf)
            img = embed_image(
                img, self._logo_path,
                ratio         = self._logo_ratio,
                ecc_level     = self._ecc,
                version       = self._version,
                shape         = self._logo_shape,
                padding       = self._logo_padding,
                padding_color = self._logo_pad_color,
                border_color  = self._logo_border,
                border_width  = self._logo_border_w,
            )
            buf = io.BytesIO()
            img.convert("RGBA" if "transparent" in self._back.lower() else "RGB").save(
                buf, format="PNG")
            buf.seek(0)

        # Post-process: frame
        if self._frame_style:
            from .extras.image_ops import add_frame
            from PIL import Image
            img = Image.open(buf)
            img = add_frame(
                img,
                style            = self._frame_style,
                frame_color      = self._frame_color,
                frame_width      = self._frame_width,
                corner_radius    = self._frame_radius,
                label            = self._label,
                label_color      = self._label_color,
                label_size       = self._label_size,
                label_position   = self._label_pos,
                background_color = self._back if self._back != "transparent" else "#FFFFFF",
            )
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)

        return buf

    def save(self, filepath: str, box_size: int | None = None, border: int | None = None) -> "QR":
        """Save QR code to a file."""
        bs = self._box_size if box_size is None else box_size
        bd = self._border if border is None else border

        
        if box_size is None:
            n_modules = self.module_count + 2 * bd
            min_px = 400
            if n_modules * bs < min_px:
                bs = max(bs, -(-min_px // n_modules))  # ceiling division
        ext = filepath.rsplit('.', 1)[-1].lower()

        if ext == "gif" and self._anim_effect:
            from .extras.animation import animate
            buf = animate(
                self._matrix,
                effect       = self._anim_effect,
                n_frames     = self._anim_frames,
                fps          = self._anim_fps,
                box_size     = bs,
                border       = bd,
                fill_color   = self._fill,
                back_color   = self._back if self._back != "transparent" else "#FFFFFF",
                module_shape = self._shape,
                finder_color = self._finder_color,
                accent_color = self._anim_accent,
                loop         = self._anim_loop,
            )
        elif ext == "gif":
            buf = self._render_static("PNG", bs, bd)
            filepath = filepath.rsplit('.', 1)[0] + ".png"
        elif ext == "svg":
            buf = self._render_static("SVG", bs, bd)
        elif ext in ("jpg", "jpeg"):
            buf = self._render_static("JPEG", bs, bd)
        else:
            buf = self._render_static("PNG", bs, bd)

        with open(filepath, 'wb') as f:
            f.write(buf.read())
        return self

    def to_pil(self, box_size: int | None = None, border: int | None = None):
        """Return a Pillow Image object."""
        from PIL import Image
        bs = self._box_size if box_size is None else box_size
        bd = self._border if border is None else border
        buf = self._render_static("PNG", bs, bd)
        return Image.open(buf)

    def to_bytes(self, format: str = "PNG") -> bytes:
        """Return raw image bytes."""
        return self.to_buffer(format).read()

    def to_buffer(self, format: str = "PNG") -> io.BytesIO:
        """Return image as BytesIO buffer."""
        fmt = format.upper()
        if fmt == "GIF" and self._anim_effect:
            from .extras.animation import animate
            return animate(
                self._matrix,
                effect=self._anim_effect, n_frames=self._anim_frames,
                fps=self._anim_fps, box_size=self._box_size,
                border=self._border, fill_color=self._fill,
                back_color=self._back if self._back != "transparent" else "#FFFFFF",
                module_shape=self._shape, finder_color=self._finder_color,
                accent_color=self._anim_accent, loop=self._anim_loop,
            )
        return self._render_static(fmt, self._box_size, self._border)

    def to_svg(self) -> str:
        """Return SVG as a string."""
        return self.to_buffer("SVG").read().decode("utf-8")

    def to_terminal(self, border: int = 2, invert: bool = False, style: str = "block") -> str:
        """Return a terminal-printable string."""
        return render_terminal(self._matrix, border=border, invert=invert, style=style)

    def show(self, border: int = 2, invert: bool = False, style: str = "block"):
        """Print QR code to the terminal."""
        print(self.to_terminal(border=border, invert=invert, style=style))
        return self

    def open(self):
        """Open the QR code in default viewer."""
        img = self.to_pil()
        img.show()
        return self

    @property
    def version(self) -> int:
        return self._version

    @property
    def ecc_level(self) -> str:
        return self._ecc

    @property
    def module_count(self) -> int:
        return len(self._matrix)

    @property
    def matrix(self) -> list[list[int]]:
        return [row[:] for row in self._matrix]

    def info(self) -> dict:
        mode_names = {1: 'numeric', 2: 'alphanumeric', 4: 'byte', 8: 'kanji'}
        return {
            'data':         self._raw[:60] + ('...' if len(self._raw) > 60 else ''),
            'type':         self._qr_type,
            'version':      self._version,
            'ecc':          self._ecc,
            'mode':         mode_names.get(self._mode, 'byte'),
            'modules':      self.module_count,
            'data_length':  len(self._raw),
        }

    @property
    def version_label(self) -> str:
        """Human-readable version label (e.g. 'v7', 'M2' for micro)."""
        if self._qr_type == "micro":
            return f"M{self._version}"
        return f"v{self._version}"

    @property
    def qr_type(self) -> str:
        return self._qr_type

    def __repr__(self) -> str:
        d = self._raw[:30]
        type_tag = f" [{self._qr_type}]" if self._qr_type != "standard" else ""
        return (f"<QR v{self._version} {self._ecc} {self.module_count}×{self.module_count}"
                f"{type_tag} {d!r}{'...' if len(self._raw)>30 else ''}>")

# ──────────────────────────────────────────────────────────────────────────
# Data helpers
# ──────────────────────────────────────────────────────────────────────────

class WiFi:
    def __init__(self, ssid: str, password: str = "", security: str = "WPA"):
        if not ssid: raise ValueError("SSID cannot be empty")
        security = security.upper()
        if security not in ("WPA", "WEP", "NOPASS", ""): security = "WPA"
        self._s, self._p, self._sec = ssid, password, security

    def __str__(self):
        return f"WIFI:T:{self._sec};S:{self._s};P:{self._p};;"

class VCard:
    def __init__(self, name: str, org: str = "", phone: str = "",
                 email: str = "", url: str = "", address: str = "", note: str = ""):
        if not name: raise ValueError("name is required")
        self.name, self.org, self.phone = name, org, phone
        self.email, self.url, self.address, self.note = email, url, address, note

    def __str__(self):
        lines = ["BEGIN:VCARD", "VERSION:3.0", f"FN:{self.name}", f"N:{self.name};;;;"]
        if self.org:     lines.append(f"ORG:{self.org}")
        if self.phone:   lines.append(f"TEL:{self.phone}")
        if self.email:   lines.append(f"EMAIL:{self.email}")
        if self.url:     lines.append(f"URL:{self.url}")
        if self.address: lines.append(f"ADR:{self.address}")
        if self.note:    lines.append(f"NOTE:{self.note}")
        lines.append("END:VCARD")
        return "\n".join(lines)

class MeCard:
    def __init__(self, name: str, phone: str = "", email: str = "",
                 url: str = "", birthday: str = "", note: str = ""):
        if not name: raise ValueError("name is required")
        self.name, self.phone, self.email = name, phone, email
        self.url, self.birthday, self.note = url, birthday, note

    def __str__(self):
        parts = [f"N:{self.name}"]
        if self.phone:    parts.append(f"TEL:{self.phone}")
        if self.email:    parts.append(f"EMAIL:{self.email}")
        if self.url:      parts.append(f"URL:{self.url}")
        if self.birthday: parts.append(f"BDAY:{self.birthday}")
        if self.note:     parts.append(f"MEMO:{self.note}")
        return "MECARD:" + ";".join(parts) + ";;"

class GeoLocation:
    def __init__(self, lat: float, lon: float, altitude: float | None = None):
        self.lat, self.lon, self.alt = lat, lon, altitude

    def __str__(self):
        s = f"geo:{self.lat},{self.lon}"
        if self.alt is not None: s += f",{self.alt}"
        return s

class Event:
    def __init__(self, summary: str, dtstart: str, dtend: str,
                 location: str = "", description: str = ""):
        self.summary, self.dtstart, self.dtend = summary, dtstart, dtend
        self.location, self.description = location, description

    def __str__(self):
        lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "BEGIN:VEVENT",
                 f"SUMMARY:{self.summary}", f"DTSTART:{self.dtstart}", f"DTEND:{self.dtend}"]
        if self.location:    lines.append(f"LOCATION:{self.location}")
        if self.description: lines.append(f"DESCRIPTION:{self.description}")
        lines += ["END:VEVENT", "END:VCALENDAR"]
        return "\n".join(lines)

class SMS:
    def __init__(self, phone: str, body: str = ""):
        self.phone, self.body = phone, body

    def __str__(self):
        return f"smsto:{self.phone}:{self.body}" if self.body else f"sms:{self.phone}"

class Email:
    def __init__(self, address: str, subject: str = "", body: str = ""):
        self.address, self.subject, self.body = address, subject, body

    def __str__(self):
        params = []
        if self.subject: params.append(f"subject={self.subject}")
        if self.body:    params.append(f"body={self.body}")
        base = f"mailto:{self.address}"
        return base + ("?" + "&".join(params) if params else "")

class Phone:
    def __init__(self, number: str):
        self.number = number

    def __str__(self):
        return f"tel:{self.number}"

class Crypto:
    def __init__(self, coin: str, address: str, amount: float | None = None,
                 label: str = "", message: str = ""):
        self.coin, self.address, self.amount = coin.lower(), address, amount
        self.label, self.message = label, message

    def __str__(self):
        params = []
        if self.amount is not None: params.append(f"amount={self.amount}")
        if self.label:              params.append(f"label={self.label}")
        if self.message:            params.append(f"message={self.message}")
        base = f"{self.coin}:{self.address}"
        return base + ("?" + "&".join(params) if params else "")

def batch(items: list, output_dir: str = ".", prefix: str = "qr", **style_kwargs) -> list[QR]:
    import os
    os.makedirs(output_dir, exist_ok=True)
    results = []
    for i, item in enumerate(items):
        if isinstance(item, tuple):
            data, filename = item
        else:
            data, filename = item, f"{prefix}_{i}.png"
        qr = QR(data)
        if style_kwargs:
            qr.style(**style_kwargs)
        qr.save(os.path.join(output_dir, filename))
        results.append(qr)
    return results