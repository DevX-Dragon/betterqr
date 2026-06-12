import warnings


class LowContrastWarning(UserWarning):
    pass


def relative_luminance(r: int, g: int, b: int) -> float:
    def linearize(v: float) -> float:
        v /= 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)


def contrast_ratio(l1: float, l2: float) -> float:
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def check_contrast(
    fill_hex: str,
    back_hex: str,
    min_ratio: float = 3.0,
    auto_fix: bool = False,
) -> tuple[str, str]:
    from .render.raster import _hex_to_rgb

    if fill_hex.strip().lower() == "transparent":
        fill_hex = "#000000"
    if back_hex.strip().lower() == "transparent":
        back_hex = "#ffffff"

    fr, fg, fb = _hex_to_rgb(fill_hex)
    br, bg, bb = _hex_to_rgb(back_hex)

    lf = relative_luminance(fr, fg, fb)
    lb = relative_luminance(br, bg, bb)
    ratio = contrast_ratio(lf, lb)

    if ratio < min_ratio:
        if auto_fix:
            lf_val = relative_luminance(fr, fg, fb)
            if lf_val > 0.5:
                fill_hex = "#000000"
            else:
                fill_hex = "#000000"
            back_hex = "#ffffff"
        else:
            warnings.warn(
                f"Contrast ratio {ratio:.2f}:1 is below {min_ratio}:1 — code may be unscannable.",
                LowContrastWarning,
                stacklevel=3,
            )

    return fill_hex, back_hex