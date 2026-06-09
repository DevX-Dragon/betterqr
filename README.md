![image](https://user-cdn.hackclub-assets.com/019ead43-13b6-784e-a116-e8c0a5fab8f0/image.png)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/github/license/DevX-Dragon/BetterQR)](https://github.com/DevX-Dragon/BetterQR/main/LICENSE)
[![PyPI - Version](https://img.shields.io/pypi/v/betterqr)](https://pypi.org/project/betterqr/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/betterqr)](https://pypi.org/project/betterqr/)
# BetterQR
BetterQR is a powerful and versatile Python library for generating beautiful, scannable QR codes with zero external QR dependencies. It offers extensive customization options, including various shapes, colors, gradients, embedded logos, frames, labels, and even animated QR codes.

## Features

- **Pure Python:** No external QR code generation libraries required.
- **Highly Customizable:** Make in any shape (square,circle,rounded,diamon.star,gapped,vertical bar,horizontal bar,), colors and background.
- **Logo Embedding:** Easily embed any logos / image into the center of the QR codes.
- **Decorative frames and labels:** Add stylish frames and text labels above or below the QR codes.
- **Animated QR codes:** Generate animated GIFs of the QR codes with effects like shimmer, fade, scan, pulse and more.
- **Data Types:** Conveniently generate QR codes for WI-FI, vCards, MeCards, Geo-Locations, SMS, Email and Phone Numbers.
- **CLI Support:** Generate QR codes directly from your terminal.
- **Multiple Output Formats:** Save QR codes as PNG, JPG, SVG, or GIF (for animations).

## Installation
BetterQR can be installed directly from PyPi using pip:
``` bash
pip install betterqr --upgrade
```

## Quick Start

### Command Line Interface (CLI)
Generate a basic QR code:
``` bash
betterqr "https://example.com"
```
Generate a styled QR code with a logo:
``` bash
betterqr "https://mysite.com" --logo logo.png --ecc H --shape circle --fill "#6C3082" --back "#F3E8FF" styled_qr.png
```
Generate an animated QR code:
``` bash
betterqr "Hello World" animated_qr.gif --effect matrix --fps 12
```

### Python Library
``` python
from betterqr import QR, WiFi, VCard

# Basic QR code
QR("https://example.com" ).save("qr_basic.png")

# Styled QR code
QR("https://example.com" ).style(shape="circle", fill="#6C3082").save("qr_styled.png")

# QR code with gradient
QR("Hello Gradient").gradient("#FF6B6B", "#4ECDC4", direction="radial").save("qr_gradient.png")

# QR code with logo (ensure 'logo.png' exists)
# For best results with logos, use ECC level H
QR("https://mysite.com", ecc="H" ).logo("logo.png", ratio=0.3, shape="rounded").save("qr_logo.png")

# Animated QR code
QR("Animated QR").animate(effect="shimmer", frames=30, fps=20).save("qr_animated.gif")

# Wi-Fi QR code
QR(WiFi("MyNetwork", "MyPassword", security="WPA")).save("qr_wifi.png")

# vCard QR code
QR(VCard("Jane Doe", phone="+1-555-1234", email="jane@example.com")).save("qr_vcard.png")
```

## Doumentations
Soon!