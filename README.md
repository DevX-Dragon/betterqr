<div align="center">

![image](https://cdn.hackclub.com/019f5645-9668-7849-8133-f085487ec59c/image.png)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![PyPI - Version](https://img.shields.io/pypi/v/betterqr)](https://pypi.org/project/betterqr/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/betterqr)](https://pypi.org/project/betterqr/)
[![CI](https://github.com/DevX-Dragon/betterqr/actions/workflows/ci.yml/badge.svg)](https://github.com/DevX-Dragon/betterqr/actions/workflows/ci.yml)
[![Hackatime - Time Spent](https://hackatime.hackclub.com/api/v1/badge/U0A0M7YSS84/devx-dragon/betterqr)](https://hackatime.hackclub.com/my/projects/33.BetterQR)

</div>

# BetterQR

BetterQR is a powerful, pure-Python QR code generator with zero external QR Generation dependencies.  
It generates beautiful, scannable codes with full control over shapes, colours, gradients,  
embedded logos, animated GIFs, Micro QR, and more.

---

## Features

| Feature | Details |
|---------|---------|
| **Standard QR** | Versions 1–40, ECC L / M / Q / H |
| **Micro QR** | All versions M1–M4 with correct auto-version selection |
| **Module shapes** | square, circle, rounded, diamond, star, gapped, vertical\_bar, horizontal\_bar |
| **Colours** | 6-char or 3-char hex (`#F00`), transparent background, separate finder colour |
| **Gradients** | horizontal, vertical, diagonal, radial |
| **Logo embedding** | square / rounded / circle shape, optional border, ratio 0.1–0.35 |
| **Frames & labels** | simple, rounded, double, shadow, fancy; label above or below |
| **Animations** | 10 GIF effects: shimmer, fade, scan, pulse, build, matrix, wave, blink, typewriter, rotate |
| **Data helpers** | WiFi, VCard, MeCard, GeoLocation, SMS, Email, Phone, Crypto |
| **Output formats** | PNG, JPG, SVG, GIF |
| **CLI** | Full-featured command-line tool |

---
<div style="text-align: center;">

## Examples

</div>

![Gallery](https://cdn.hackclub.com/019f66b9-6f53-71ef-ac25-5b19351a6ee2/image.png)

## Installation

```bash
pip install betterqr --upgrade
```

---

## Why BetterQR?

| | BetterQR | `qrcode` | `segno` |
|---|:---:|:---:|:---:|
| Zero external QR-gen dependencies | ✅ | ✅ | ✅ |
| Module shapes (circle, star, diamond, etc.) | ✅ | ❌ | ❌ |
| Gradients | ✅ | ❌ | ❌ |
| Logo embedding | ✅ | Manual (Pillow) | ❌ |
| Frames & labels | ✅ | ❌ | ❌ |
| Animated GIF output | ✅ | ❌ | ❌ |
| Micro QR (M1–M4) | ✅ | ❌ | ✅ |
| WiFi / vCard / MeCard / SMS / Email / Phone helpers | ✅ | ❌ | Partial |
| CLI included | ✅ | ✅ | ✅ |
| SVG / PDF / EPS output | ✅ | SVG only | ✅ |

---

## Quick Start

### CLI

```bash
# Basic QR code
betterqr "https://example.com" my_qr.png

# Micro QR (auto-selects smallest version)
betterqr "HELLO" --type micro micro.png

# Styled with gradient
betterqr "Hello" my_qr.png --gradient "#FF6B6B" "#4ECDC4" --gradient-dir radial

# With logo (use ECC H for logos)
betterqr "https://mysite.com" qr.png --logo logo.png --logo-ratio 0.3 --logo-shape rounded -e H

# Animated GIF
betterqr "Animated QR" animated.gif --effect matrix --fps 12

# WiFi
betterqr --wifi MySSID MyPassword output.png

# Contact
betterqr --contact "Jane Doe" --phone "+1-555-1234" --email "jane@example.com" contact.png
```

### Python API

```python
from betterqr import QR, WiFi, VCard, GeoLocation, SMS, Email, Phone

# Basic
QR("https://example.com").save("qr.png")

# Micro QR — all versions
QR("1234",        qr_type="micro", version=1, ecc="M").save("m1.png")  # numeric only
QR("HELLO WORLD", qr_type="micro", version=3, ecc="M").save("m3.png")  # alphanumeric
QR("Hello!",      qr_type="micro", version=4, ecc="L").save("m4.png")  # byte mode

# Styling
(QR("styled")
    .style(shape="circle", fill="#6C3082", back="#F3E8FF")
    .save("styled.png"))

# 3-char hex works too
QR("x").style(fill="#000", back="#FFF").save("mono.png")

# Gradient
QR("gradient").gradient("#FF6B6B", "#4ECDC4", direction="radial").save("grad.png")

# Logo (border=True adds a thin outline around the logo)
(QR("https://mysite.com", ecc="H")
    .logo("logo.png", ratio=0.25, shape="rounded", border=True)
    .save("logo.png"))

# Frame + label
(QR("https://example.com")
    .frame("fancy")
    .label("Scan Me!", position="below")
    .save("framed.png"))

# Animation
QR("Hello", ecc="H", version=4).animate("matrix", frames=30, fps=15).save("anim.gif")

# Data helpers — pass the helper directly or convert to string
QR(WiFi("MyNet", "MyPass", "WPA")).save("wifi.png")
QR(GeoLocation(51.5074, -0.1278)).save("geo.png")
QR(SMS("+15550199", "Hello!")).save("sms.png")
QR(Email("hi@example.com")).save("email.png")
QR(Phone("+18005550199")).save("phone.png")
QR(VCard("Jane Doe", phone="+15550199", email="jane@example.com")).save("vcard.png")
```

---

## Micro QR Capacities

| Symbol | Size | Max Numeric | Max Alpha | Max Bytes |
|--------|------|-------------|-----------|-----------|
| M1/M   | 11×11 | 5          | —         | —         |
| M2/L   | 13×13 | 10         | 6         | —         |
| M2/M   | 13×13 | 8          | 5         | —         |
| M3/L   | 15×15 | 23         | 14        | 9         |
| M3/M   | 15×15 | 18         | 11        | 7         |
| M4/L   | 17×17 | 35         | 21        | 15        |
| M4/M   | 17×17 | 30         | 18        | 13        |
| M4/Q   | 17×17 | 21         | 13        | 9         |

> [!NOTE]
> Micro QR does not support ECC H. Use standard QR for logos.
> Micro QR cannot be scanned using normal phone cameras

> [!TIP]
> Use a dedicated [Micro QR scanner](https://www.dynamsoft.com/barcode-reader/barcode-types/micro-qr-code/) to test the microqr codes


---

## Documentation
Check out the [DOCUMENTATION](docs/DOCUMENTATION.md) for an better overview of BetterQR

## License
Regsitred under MIT LISCENSE — see [LICENSE](LICENSE)
