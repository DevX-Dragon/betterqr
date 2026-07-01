# BetterQR Documentation v2.0.0

Welcome to the comprehensive documentation for BetterQR, a powerful and flexible Python library for generating highly customizable QR codes. This document covers everything from installation and basic usage to advanced styling, animation, and data type shortcuts.

## Table of Contents

1. [Introduction](#1-introduction)
2. [Installation](#2-installation)
3. [Command-Line Interface (CLI)](#3-command-line-interface-cli)
   - [Basic Usage](#basic-usage)
   - [QR Settings](#qr-settings)
   - [Styling](#styling)
   - [Gradients](#gradients)
   - [Logo Embedding](#logo-embedding)
   - [Frames & Labels](#frames--labels)
   - [Animation](#animation)
   - [Data Type Shortcuts](#data-type-shortcuts)
   - [Output & Terminal Preview](#output--terminal-preview)
4. [Python API](#4-python-api)
   - [QR Class](#qr-class)
     - [Initialization](#initialization)
     - [Styling Methods](#styling-methods)
     - [Logo Methods](#logo-methods)
     - [Frame & Label Methods](#frame--label-methods)
     - [Animation Methods](#animation-methods)
     - [Output Methods](#output-methods)
     - [Metadata Properties](#metadata-properties)
   - [Data Helper Classes](#data-helper-classes)
     - [WiFi](#wifi)
     - [VCard](#vcard)
     - [MeCard](#mecard)
     - [GeoLocation](#geolocation)
     - [Event](#event)
     - [SMS](#sms)
     - [Email](#email)
     - [Phone](#phone)
     - [Crypto](#crypto)
   - [Batch Generation](#batch-generation)
5. [Advanced Topics](#5-advanced-topics)
   - [Micro QR Codes](#micro-qr-codes)
   - [Error Correction Levels](#error-correction-levels)
   - [Transparent Backgrounds](#transparent-backgrounds)
   - [Contrast Guard & Dark Mode](#contrast-guard--dark-mode)
   - [Logo Sizing and Scannability](#logo-sizing-and-scannability)
6. [Troubleshooting](#6-troubleshooting)
7. [Contributing](#7-contributing)
8. [License](#8-license)

---

## 1. Introduction

BetterQR is a Python library designed to generate highly customizable QR codes. Unlike many other QR code libraries, BetterQR is built from the ground up in pure Python, meaning it has zero external dependencies for the core QR generation logic. It provides both a convenient command-line interface (CLI) for quick generation and a flexible Python API for programmatic control.

Key features include advanced visual styling options such as custom module shapes, gradient fills, embedded logos, decorative frames, and even animated QR codes. It also simplifies the creation of complex data-type QR codes (e.g., Wi-Fi, vCard, Crypto) through dedicated helper classes. **Version 2.0.0** introduces Micro QR support, enhanced animation effects, and terminal preview capabilities.

## 2. Installation

BetterQR can be easily installed using `pip`:

```bash
pip install betterqr
```

For development purposes, you can install from source:

```bash
```bash
git clone https://github.com/DevX-Dragon/BetterQR.git
cd BetterQR
pip install -e .
```

---

## 3. Command-Line Interface (CLI)

The `betterqr` command provides a rich set of options for generating QR codes directly from your terminal. The basic syntax is:

```bash
betterqr <data> [output_file] [options]
```

If `output_file` is omitted, it defaults to `qr.png`.

### Basic Usage

Generate a simple QR code for a URL:

```bash
betterqr "https://www.example.com" my_qr.png
```

Generate a QR code for plain text:

```bash
betterqr "Hello, BetterQR!" text_qr.png
```

Display a QR code in the terminal:

```bash
betterqr "https://example.com" --print
```

### QR Settings

These options control the fundamental properties of the QR code:

| Option | Short | Description |
|--------|-------|-------------|
| `--type` | | QR code type: `standard` (v1-40) or `micro` (M1-M4) [default: standard] |
| `--ecc` | `-e` | Error correction level: `L`, `M`, `Q`, `H` (default: `M`). Micro QR supports L/M/Q. |
| `--version` | `-v` | QR code version (1-40 for standard, 1-4 for micro; auto-detected by default) |
| `--box-size` | `-b` | Size of each module in pixels (default: 10) |
| `--border` | `-bd` | Border size in modules (default: 4) |

Example:

```bash
betterqr "https://example.com" qr.png --type micro --ecc L
```

### Styling

Customize the appearance of your QR code with various styling options:

| Option | Short | Description |
|--------|-------|-------------|
| `--fill` | `-f` | Fill color in hex format or `transparent` (default: `#000000`) |
| `--back` | `-bk` | Background color in hex format or `transparent` (default: `#FFFFFF`) |
| `--shape` | `-s` | Module shape: `square`, `circle`, `rounded`, `diamond`, `star`, `gapped`, `vertical_bar`, `horizontal_bar` (default: `square`) |
| `--finder`| | Separate color for the 3 finder squares |

Example:

```bash
betterqr "https://example.com" styled_qr.png --fill "#6C3082" --back "#F3E8FF" --shape circle --finder "#FF0000"
```

### Gradients

Apply stunning gradient fills to your QR code:

| Option | Short | Description |
|--------|-------|-------------|
| `--gradient` | | Two colors for a gradient fill. Example: `--gradient "#FF6B6B" "#4ECDC4"` |
| `--gradient-dir` | `-gd` | Gradient direction: `horizontal`, `vertical`, `diagonal`, `radial` (default: `diagonal`) |

Example:

```bash
betterqr "Hello Gradient" gradient_qr.png --gradient "#FF6B6B" "#4ECDC4" --gradient-dir radial
```

### Logo Embedding

Embed logos or images in the center of your QR code:

| Option | Short | Description |
|--------|-------|-------------|
| `--logo` | `-l` | Path to logo image file |
| `--logo-ratio` | `-lr` | Logo size ratio (0.1-0.35, default: 0.25) |
| `--logo-shape` | `-ls` | Logo shape: `square`, `circle`, `rounded` (default: `square`) |

Example:

```bash
betterqr "https://mysite.com" qr_with_logo.png --logo logo.png --logo-ratio 0.3 --logo-shape rounded --ecc H
```

**Note:** Use error correction level `H` when embedding logos for better scannability.

### Frames & Labels

Add decorative frames and text labels to your QR codes:

| Option | Short | Description |
|--------|-------|-------------|
| `--frame` | `-fr` | Frame style: `simple`, `rounded`, `double`, `shadow`, `fancy` |
| `--frame-color` | `-fc` | Frame color in hex format |
| `--label` | `-lb` | Text label to display |
| `--label-above` | | Place label above the QR instead of below |
| `--label-size` | | Label font size in pixels (default: 14) |
| `--label-color` | | Label text color in hex format (default: `#000000`) |

Example:

```bash
betterqr "https://example.com" framed_qr.png --frame fancy --label "Scan Me!" --label-above
```

### Animation

Generate animated QR codes with various effects:

| Option | Short | Description |
|--------|-------|-------------|
| `--effect` | `-eff` | Animation effect: `shimmer`, `fade`, `scan`, `pulse`, `build`, `matrix`, `wave`, `blink`, `typewriter`, `rotate` |
| `--frames` | `-fr` | Number of animation frames (default: 20) |
| `--fps` | `-fps` | Frames per second (default: 15) |
| `--accent` | | Accent color for effects like `rotate` or `typewriter` |

Example:

```bash
betterqr "Animated QR" animated_qr.gif --effect rotate --accent "#3B82F6" --frames 30 --fps 15
```

### Data Type Shortcuts

Generate QR codes for specific data types using convenient shortcuts:

#### WiFi QR Code
```bash
betterqr --wifi MySSID MyPassword --security WPA
```

#### vCard (Contact) QR Code
```bash
betterqr --contact "Jane Doe" --phone "+1-555-1234" --email "jane@example.com" --org "Acme Corp"
```

#### SMS QR Code
```bash
betterqr --sms "+1-555-1234" "Hello World"
```

#### Email QR Code
```bash
betterqr --email "user@example.com" "Subject" "Message Body"
```

#### Phone QR Code
```bash
betterqr --phone "+1-555-1234"
```

#### Geo-Location QR Code
```bash
betterqr --geo 40.7128 -74.0060
```

### Output & Terminal Preview

| Option | Short | Description |
|--------|-------|-------------|
| `--print` | | Print QR code to terminal |
| `--invert`| | Invert terminal colors (for dark-background terminals) |
| `--terminal-style` | | Terminal render style: `block`, `ascii`, `compact` (default: `block`) |
| `--info`  | | Print QR code metadata (version, size, mode, etc.) |

---

## 4. Python API

### QR Class

The `QR` class is the core of BetterQR, providing a flexible API for generating customized QR codes programmatically.

#### Initialization

```python
from betterqr import QR

# Basic initialization
qr = QR("https://example.com")

# With custom settings
qr = QR(
    data="https://example.com",
    ecc="H",  # Error correction level
    version=None,  # Auto-detect
    qr_type="standard"  # "standard" or "micro"
)
```

**Parameters:**
- `data` (str): The data to encode in the QR code
- `ecc` (str): Error correction level - `L`, `M`, `Q`, or `H` (default: `M`)
- `version` (int, optional): QR code version (1-40 for standard, 1-4 for micro). If None, auto-detected
- `qr_type` (str): `standard` or `micro` (default: `standard`)

#### Styling Methods

**style()** - Apply styling to the QR code

```python
qr = QR("https://example.com").style(
    fill="#6C3082",
    back="#F3E8FF",
    shape="circle",
    finder="#FF0000",
    box_size=10,
    border=4,
    dark_mode=False,
    auto_fix_contrast=False
)
qr.save("styled_qr.png")
```

**Parameters:**
- `fill` (str): Fill color in hex format (default: `#000000`)
- `back` (str): Background color in hex format (default: `#FFFFFF`)
- `shape` (str): Module shape - `square`, `circle`, `rounded`, `diamond`, `star`, `gapped`, `vertical_bar`, `horizontal_bar`
- `finder` (str): Separate color for finder patterns
- `box_size` (int): Pixels per module
- `border` (int): Quiet zone width in modules
- `dark_mode` (bool): Invert colors and optimize for dark themes
- `auto_fix_contrast` (bool): Automatically adjust fill color if contrast is too low

**gradient()** - Apply gradient fill to the QR code

```python
qr = QR("Hello Gradient").gradient(
    start_color="#FF6B6B",
    end_color="#4ECDC4",
    direction="radial"
)
qr.save("gradient_qr.png")
```

**Parameters:**
- `start_color` (str): Starting color in hex format
- `end_color` (str): Ending color in hex format
- `direction` (str): `linear`, `radial`, `horizontal`, `vertical`, `diagonal` (default: `diagonal`)

#### Logo Methods

**logo()** - Embed a logo in the QR code

```python
qr = QR("https://mysite.com", ecc="H").logo(
    path="logo.png",
    ratio=0.25,
    shape="rounded",
    padding=2,
    padding_color="#FFFFFF",
    border=0,
    border_width=2
)
qr.save("qr_with_logo.png")
```

**Parameters:**
- `path` (str): Path to the logo image file
- `ratio` (float): Logo size ratio (0.1-0.35, default: 0.25)
- `shape` (str): Logo shape - `square`, `circle`, `rounded` (default: `square`)
- `padding` (int): Padding around logo in pixels (default: 2)
- `padding_color` (str): Color of the padding area
- `border` (int): Border color (if any)
- `border_width` (int): Width of the logo border

#### Frame & Label Methods

**frame()** - Add a decorative frame

```python
qr = QR("https://example.com").frame(
    style="shadow",
    color="#333333",
    width=40,
    radius=20,
    label="Visit Us!",
    label_position="bottom"
)
qr.save("framed_qr.png")
```

**Parameters:**
- `style` (str): Frame style - `simple`, `rounded`, `double`, `shadow`, `fancy`
- `color` (str): Frame color in hex format
- `width` (int): Frame width in pixels
- `radius` (int): Corner radius for rounded frames
- `label` (str): Optional text label
- `label_position` (str): `top` or `bottom`

**label()** - Shortcut to add a text label

```python
qr = QR("https://example.com").label(
    text="Visit Us!",
    color="#000000",
    size=14,
    position="bottom"
)
```

#### Animation Methods

**animate()** - Create an animated QR code

```python
qr = QR("Animated QR").animate(
    effect="matrix",
    frames=30,
    fps=15,
    accent="#3B82F6"
)
qr.save("animated_qr.gif")
```

**Parameters:**
- `effect` (str): Animation effect - `shimmer`, `fade`, `scan`, `pulse`, `build`, `matrix`, `wave`, `blink`, `typewriter`, `rotate`
- `frames` (int): Number of animation frames (default: 20)
- `fps` (int): Frames per second (default: 15)
- `accent` (str): Accent color for certain effects
- `loop` (int): Number of loops (0 for infinite)

#### Output Methods

**save()** - Save the QR code to a file
```python
qr.save("qr.png") # Supports .png, .jpg, .svg, .gif, .pdf
```

**to_terminal()** - Get terminal-formatted string
```python
print(qr.to_terminal(style="compact", invert=True))
```

**info()** - Get metadata dictionary
```python
print(qr.info()) # Returns version, ecc, type, size, etc.
```

#### Metadata Properties

- `version_label`: Human-readable version (e.g., 'v7', 'M2')
- `qr_type`: "standard" or "micro"
- `module_count`: Number of modules across one side

---

### Data Helper Classes

BetterQR provides convenient helper classes for generating QR codes for specific data types.

#### WiFi
```python
from betterqr import QR, WiFi
wifi = WiFi(ssid="MyNetwork", password="SecurePassword123", security="WPA")
qr = QR(wifi).save("wifi_qr.png")
```

#### VCard
```python
from betterqr import QR, VCard
vcard = VCard(name="Jane Doe", phone="+1-555-1234", email="jane@example.com", org="Acme Corp")
qr = QR(vcard).save("contact_qr.png")
```

#### MeCard
```python
from betterqr import QR, MeCard
mecard = MeCard(name="John Smith", phone="+1-555-5678", email="john@example.com")
qr = QR(mecard).save("mecard_qr.png")
```

#### GeoLocation
```python
from betterqr import QR, GeoLocation
geo = GeoLocation(lat=40.7128, lon=-74.0060, altitude=10)
qr = QR(geo).save("location_qr.png")
```

#### Event
```python
from betterqr import QR, Event
event = Event(summary="Meeting", dtstart="20240615T090000", dtend="20240615T100000")
qr = QR(event).save("event_qr.png")
```

#### SMS
```python
from betterqr import QR, SMS
sms = SMS(phone="+1-555-1234", body="Hello!")
qr = QR(sms).save("sms_qr.png")
```

#### Email
```python
from betterqr import QR, Email
email = Email(address="user@example.com", subject="Hello", body="Body text")
qr = QR(email).save("email_qr.png")
```

#### Phone
```python
from betterqr import QR, Phone
phone = Phone(number="+1-555-1234")
qr = QR(phone).save("phone_qr.png")
```

#### Crypto
```python
from betterqr import QR, Crypto
crypto = Crypto(coin="bitcoin", address="1A1z7agoat2LLLLL...", amount=0.5)
qr = QR(crypto).save("crypto_qr.png")
```

### Batch Generation

Generate multiple QR codes efficiently:

```python
from betterqr import batch
items = [
    ("https://example1.com", "qr1.png"),
    ("https://example2.com", "qr2.png")
]
batch(items, output_dir="qrs", fill="#1D4ED8", shape="rounded")
```

---

## 5. Advanced Topics

### Micro QR Codes
Micro QR codes are a compact version of standard QR codes, designed for applications where space is extremely limited. They support versions M1 to M4.
- **M1**: 11x11 modules, up to 35 numeric characters.
- **M4**: 17x17 modules, up to 35 alphanumeric characters with ECC level M.
Note: Micro QR does not support ECC level 'H' or large logos.

### Error Correction Levels
| Level | Recovery | Use Case |
|-------|----------|----------|
| L | ~7% | General use, low risk |
| M | ~15% | Standard use, recommended |
| Q | ~25% | High-risk environments |
| H | ~30% | With logos or heavy styling |

### Transparent Backgrounds
Generate QR codes with transparent backgrounds by setting `back="transparent"` in the `style()` method. This is only supported for PNG and SVG formats.

### Contrast Guard & Dark Mode
BetterQR includes a **Luminance Guard** that calculates the contrast ratio between your fill and background colors. If the ratio is below 4.5 (WCAG standard), a `LowContrastWarning` is issued.
Using `dark_mode=True` in `style()` will automatically invert colors for dark backgrounds and enable `auto_fix_contrast` to ensure scannability.

---

## 6. Troubleshooting

### QR Code Not Scanning
1. **Increase ECC**: Use `ecc="H"`.
2. **Check Contrast**: Ensure high contrast between fill and back colors.
3. **Logo Size**: Reduce `logo_ratio` to 0.2.
4. **Quiet Zone**: Ensure `border` is at least 4.

### Animation Issues
1. **Format**: Ensure filename ends in `.gif`.
2. **Frames**: Use at least 20 frames for smooth effects.
3. **Complexity**: Some readers struggle with high-speed animations; keep `fps` between 10-20.

## 7. Contributing
We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md).

## 8. License
BetterQR is released under the MIT License.

---
**Last Updated:** 2026
**Version:** 2.0.0
