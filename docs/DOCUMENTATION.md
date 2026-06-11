# BetterQR Documentation

Welcome to the comprehensive documentation for BetterQR, a powerful and flexible Python library for generating highly customizable QR codes. This document covers everything from installation and basic usage to advanced styling, animation, and data type shortcuts.

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Command-Line Interface (CLI)](#command-line-interface-cli)
   - [Basic Usage](#basic-usage)
   - [QR Settings](#qr-settings)
   - [Styling](#styling)
   - [Gradients](#gradients)
   - [Logo Embedding](#logo-embedding)
   - [Frames & Labels](#frames--labels)
   - [Animation](#animation)
   - [Data Type Shortcuts](#data-type-shortcuts)
   - [Output Options](#output-options)
4. [Python API](#python-api)
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
5. [Advanced Topics](#advanced-topics)
   - [Error Correction Levels](#error-correction-levels)
   - [Transparent Backgrounds](#transparent-backgrounds)
   - [Logo Sizing and Scannability](#logo-sizing-and-scannability)
6. [Troubleshooting](#troubleshooting)
7. [Contributing](#contributing)
8. [License](#license)

## 1. Introduction

BetterQR is a Python library designed to generate highly customizable QR codes. Unlike many other QR code libraries, BetterQR is built from the ground up in pure Python, meaning it has zero external dependencies for the core QR generation logic. It provides both a convenient command-line interface (CLI) for quick generation and a flexible Python API for programmatic control.

Key features include advanced visual styling options such as custom module shapes, gradient fills, embedded logos, decorative frames, and even animated QR codes. It also simplifies the creation of complex data-type QR codes (e.g., Wi-Fi, vCard) through dedicated helper classes.

## 2. Installation

BetterQR can be easily installed using `pip`:

```bash
pip install betterqr
```

For development purposes, you can install from source:

```bash
git clone https://github.com/DevX-Dragon/BetterQR.git
cd BetterQR
pip install -e .
```

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
betterqr "https://example.com" --display
```

### QR Settings

These options control the fundamental properties of the QR code:

| Option | Short | Description |
|--------|-------|-------------|
| `--ecc` | `-e` | Error correction level: `L`, `M`, `Q`, `H` (default: `M`) |
| `--version` | `-v` | QR code version (1-40, auto-detected by default) |
| `--box-size` | `-b` | Size of each module in pixels (default: 10) |
| `--border` | `-bd` | Border size in modules (default: 4) |

Example:

```bash
betterqr "https://example.com" qr.png --ecc H --box-size 15 --border 2
```

### Styling

Customize the appearance of your QR code with various styling options:

| Option | Short | Description |
|--------|-------|-------------|
| `--fill` | `-f` | Fill color in hex format (default: `#000000`) |
| `--back` | `-bk` | Background color in hex format (default: `#FFFFFF`) |
| `--shape` | `-s` | Module shape: `square`, `circle`, `rounded`, `diamond`, `star`, `gapped`, `vbar`, `hbar` (default: `square`) |
| `--radius` | `-r` | Corner radius for rounded shapes (0-1, default: 0.5) |

Example:

```bash
betterqr "https://example.com" styled_qr.png --fill "#6C3082" --back "#F3E8FF" --shape circle --radius 0.8
```

### Gradients

Apply stunning gradient fills to your QR code:

| Option | Short | Description |
|--------|-------|-------------|
| `--gradient-start` | `-gs` | Starting color for gradient in hex format |
| `--gradient-end` | `-ge` | Ending color for gradient in hex format |
| `--gradient-direction` | `-gd` | Gradient direction: `linear`, `radial` (default: `linear`) |
| `--gradient-angle` | `-ga` | Angle for linear gradient in degrees (0-360, default: 45) |

Example:

```bash
betterqr "Hello Gradient" gradient_qr.png --gradient-start "#FF6B6B" --gradient-end "#4ECDC4" --gradient-direction radial
```

### Logo Embedding

Embed logos or images in the center of your QR code:

| Option | Short | Description |
|--------|-------|-------------|
| `--logo` | `-l` | Path to logo image file |
| `--logo-ratio` | `-lr` | Logo size ratio (0-0.4, default: 0.3) |
| `--logo-shape` | `-ls` | Logo shape: `square`, `circle`, `rounded` (default: `square`) |
| `--logo-padding` | `-lp` | Padding around logo (0-0.2, default: 0.05) |

Example:

```bash
betterqr "https://mysite.com" qr_with_logo.png --logo logo.png --logo-ratio 0.3 --logo-shape rounded --ecc H
```

**Note:** Use error correction level `H` when embedding logos for better scannability.

### Frames & Labels

Add decorative frames and text labels to your QR codes:

| Option | Short | Description |
|--------|-------|-------------|
| `--frame` | `-fr` | Frame style: `simple`, `rounded`, `double`, `shadow` |
| `--frame-color` | `-fc` | Frame color in hex format |
| `--label` | `-lb` | Text label to display |
| `--label-position` | `-lbp` | Label position: `top`, `bottom` (default: `bottom`) |
| `--label-font-size` | `-lbfs` | Label font size in pixels (default: 20) |
| `--label-color` | `-lbc` | Label text color in hex format (default: `#000000`) |

Example:

```bash
betterqr "https://example.com" framed_qr.png --frame shadow --frame-color "#333333" --label "Visit Us!" --label-position top
```

### Animation

Generate animated QR codes with various effects:

| Option | Short | Description |
|--------|-------|-------------|
| `--effect` | `-eff` | Animation effect: `shimmer`, `fade`, `scan`, `pulse`, `matrix`, `wave` |
| `--frames` | `-fr` | Number of animation frames (default: 20) |
| `--fps` | `-fps` | Frames per second (default: 10) |
| `--duration` | `-dur` | Total animation duration in seconds |

Example:

```bash
betterqr "Animated QR" animated_qr.gif --effect matrix --frames 30 --fps 12
```

### Data Type Shortcuts

Generate QR codes for specific data types using convenient shortcuts:

#### WiFi QR Code

```bash
betterqr wifi "MyNetwork:MyPassword:WPA" wifi_qr.png
```

#### vCard (Contact) QR Code

```bash
betterqr vcard "Jane Doe:+1-555-1234:jane@example.com:Acme Corp" vcard_qr.png
```

#### SMS QR Code

```bash
betterqr sms "+1-555-1234:Hello World" sms_qr.png
```

#### Email QR Code

```bash
betterqr email "user@example.com:Subject:Message Body" email_qr.png
```

#### Phone QR Code

```bash
betterqr phone "+1-555-1234" phone_qr.png
```

#### Geo-Location QR Code

```bash
betterqr geo "40.7128:-74.0060" geo_qr.png
```

### Output Options

| Option | Short | Description |
|--------|-------|-------------|
| `--format` | `-fmt` | Output format: `png`, `jpg`, `svg`, `gif` (default: `png`) |
| `--quality` | `-q` | JPEG quality (0-100, default: 95) |
| `--display` | `-d` | Display QR code in terminal instead of saving |
| `--optimize` | `-opt` | Optimize output file size |

Example:

```bash
betterqr "https://example.com" qr.svg --format svg
```

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
    box_size=10,
    border=4
)
```

**Parameters:**
- `data` (str): The data to encode in the QR code
- `ecc` (str): Error correction level - `L`, `M`, `Q`, or `H` (default: `M`)
- `version` (int, optional): QR code version (1-40). If None, auto-detected
- `box_size` (int): Size of each module in pixels (default: 10)
- `border` (int): Border size in modules (default: 4)

#### Styling Methods

**style()** - Apply styling to the QR code

```python
qr = QR("https://example.com").style(
    fill_color="#6C3082",
    back_color="#F3E8FF",
    shape="circle",
    radius=0.8
)
qr.save("styled_qr.png")
```

**Parameters:**
- `fill_color` (str): Fill color in hex format (default: `#000000`)
- `back_color` (str): Background color in hex format (default: `#FFFFFF`)
- `shape` (str): Module shape - `square`, `circle`, `rounded`, `diamond`, `star`, `gapped`, `vbar`, `hbar`
- `radius` (float): Corner radius for rounded shapes (0-1)

**gradient()** - Apply gradient fill to the QR code

```python
qr = QR("Hello Gradient").gradient(
    start_color="#FF6B6B",
    end_color="#4ECDC4",
    direction="radial",
    angle=45
)
qr.save("gradient_qr.png")
```

**Parameters:**
- `start_color` (str): Starting color in hex format
- `end_color` (str): Ending color in hex format
- `direction` (str): `linear` or `radial` (default: `linear`)
- `angle` (int): Angle for linear gradient in degrees (0-360)

#### Logo Methods

**logo()** - Embed a logo in the QR code

```python
qr = QR("https://mysite.com", ecc="H").logo(
    image_path="logo.png",
    ratio=0.3,
    shape="rounded",
    padding=0.05
)
qr.save("qr_with_logo.png")
```

**Parameters:**
- `image_path` (str): Path to the logo image file
- `ratio` (float): Logo size ratio (0-0.4, default: 0.3)
- `shape` (str): Logo shape - `square`, `circle`, `rounded` (default: `square`)
- `padding` (float): Padding around logo (0-0.2, default: 0.05)

#### Frame & Label Methods

**frame()** - Add a decorative frame

```python
qr = QR("https://example.com").frame(
    style="shadow",
    color="#333333",
    width=20
)
qr.save("framed_qr.png")
```

**Parameters:**
- `style` (str): Frame style - `simple`, `rounded`, `double`, `shadow`
- `color` (str): Frame color in hex format
- `width` (int): Frame width in pixels

**label()** - Add a text label

```python
qr = QR("https://example.com").label(
    text="Visit Us!",
    position="top",
    font_size=20,
    color="#000000"
)
qr.save("labeled_qr.png")
```

**Parameters:**
- `text` (str): Label text
- `position` (str): `top` or `bottom` (default: `bottom`)
- `font_size` (int): Font size in pixels (default: 20)
- `color` (str): Text color in hex format

#### Animation Methods

**animate()** - Create an animated QR code

```python
qr = QR("Animated QR").animate(
    effect="matrix",
    frames=30,
    fps=12
)
qr.save("animated_qr.gif")
```

**Parameters:**
- `effect` (str): Animation effect - `shimmer`, `fade`, `scan`, `pulse`, `matrix`, `wave`
- `frames` (int): Number of animation frames (default: 20)
- `fps` (int): Frames per second (default: 10)
- `duration` (float, optional): Total animation duration in seconds

#### Output Methods

**save()** - Save the QR code to a file

```python
qr = QR("https://example.com").save(
    filename="qr.png",
    format="png",
    quality=95
)
```

**Parameters:**
- `filename` (str): Output filename
- `format` (str): Output format - `png`, `jpg`, `svg`, `gif` (auto-detected from filename)
- `quality` (int): JPEG quality (0-100, default: 95)

**display()** - Display the QR code in the terminal

```python
qr = QR("https://example.com").display()
```

**get_image()** - Get the QR code as a PIL Image object

```python
qr = QR("https://example.com")
image = qr.get_image()
# Use PIL Image methods
image.show()
```

#### Metadata Properties

**version** - Get the QR code version

```python
qr = QR("https://example.com")
print(qr.version)  # Returns the version number
```

**data_capacity** - Get the data capacity for the current version

```python
qr = QR("https://example.com")
print(qr.data_capacity)  # Returns the maximum data capacity
```

**size** - Get the QR code size in pixels

```python
qr = QR("https://example.com")
print(qr.size)  # Returns the size in pixels
```

### Data Helper Classes

BetterQR provides convenient helper classes for generating QR codes for specific data types.

#### WiFi

Generate WiFi connection QR codes:

```python
from betterqr import QR, WiFi

wifi = WiFi(
    ssid="MyNetwork",
    password="SecurePassword123",
    security="WPA",  # WPA, WEP, or nopass
    hidden=False
)

qr = QR(wifi)
qr.save("wifi_qr.png")
```

**Parameters:**
- `ssid` (str): Network name
- `password` (str): Network password
- `security` (str): Security type - `WPA`, `WEP`, `nopass` (default: `WPA`)
- `hidden` (bool): Whether the network is hidden (default: False)

#### VCard

Generate contact information QR codes:

```python
from betterqr import QR, VCard

vcard = VCard(
    name="Jane Doe",
    phone="+1-555-1234",
    email="jane@example.com",
    organization="Acme Corp",
    url="https://example.com",
    address="123 Main St, City, State 12345"
)

qr = QR(vcard)
qr.save("contact_qr.png")
```

**Parameters:**
- `name` (str): Full name
- `phone` (str, optional): Phone number
- `email` (str, optional): Email address
- `organization` (str, optional): Organization name
- `url` (str, optional): Website URL
- `address` (str, optional): Physical address

#### MeCard

Generate MeCard format contact QR codes (compatible with older devices):

```python
from betterqr import QR, MeCard

mecard = MeCard(
    name="John Smith",
    phone="+1-555-5678",
    email="john@example.com",
    url="https://example.com"
)

qr = QR(mecard)
qr.save("mecard_qr.png")
```

**Parameters:**
- `name` (str): Full name
- `phone` (str, optional): Phone number
- `email` (str, optional): Email address
- `url` (str, optional): Website URL

#### GeoLocation

Generate location-based QR codes:

```python
from betterqr import QR, GeoLocation

geo = GeoLocation(
    latitude=40.7128,
    longitude=-74.0060,
    altitude=10,  # Optional
    query="New York City"  # Optional
)

qr = QR(geo)
qr.save("location_qr.png")
```

**Parameters:**
- `latitude` (float): Latitude coordinate
- `longitude` (float): Longitude coordinate
- `altitude` (float, optional): Altitude in meters
- `query` (str, optional): Location query string

#### Event

Generate calendar event QR codes:

```python
from betterqr import QR, Event

event = Event(
    title="Conference 2024",
    start_time="20240615T090000",
    end_time="20240615T170000",
    location="Convention Center",
    description="Annual tech conference"
)

qr = QR(event)
qr.save("event_qr.png")
```

**Parameters:**
- `title` (str): Event title
- `start_time` (str): Start time in format YYYYMMDDTHHMMSS
- `end_time` (str): End time in format YYYYMMDDTHHMMSS
- `location` (str, optional): Event location
- `description` (str, optional): Event description

#### SMS

Generate SMS message QR codes:

```python
from betterqr import QR, SMS

sms = SMS(
    phone_number="+1-555-1234",
    message="Hello from BetterQR!"
)

qr = QR(sms)
qr.save("sms_qr.png")
```

**Parameters:**
- `phone_number` (str): Recipient phone number
- `message` (str, optional): Message text

#### Email

Generate email QR codes:

```python
from betterqr import QR, Email

email = Email(
    address="user@example.com",
    subject="Hello",
    body="This is a test email"
)

qr = QR(email)
qr.save("email_qr.png")
```

**Parameters:**
- `address` (str): Email address
- `subject` (str, optional): Email subject
- `body` (str, optional): Email body

#### Phone

Generate phone call QR codes:

```python
from betterqr import QR, Phone

phone = Phone(phone_number="+1-555-1234")

qr = QR(phone)
qr.save("phone_qr.png")
```

**Parameters:**
- `phone_number` (str): Phone number to call

#### Crypto

Generate cryptocurrency payment QR codes:

```python
from betterqr import QR, Crypto

crypto = Crypto(
    currency="bitcoin",  # bitcoin, ethereum, etc.
    address="1A1z7agoat2LLLLL...",
    amount=0.5
)

qr = QR(crypto)
qr.save("crypto_qr.png")
```

**Parameters:**
- `currency` (str): Cryptocurrency type
- `address` (str): Wallet address
- `amount` (float, optional): Amount to send

### Batch Generation

Generate multiple QR codes efficiently:

```python
from betterqr import QR

data_list = [
    "https://example1.com",
    "https://example2.com",
    "https://example3.com"
]

for i, data in enumerate(data_list):
    qr = QR(data)
    qr.save(f"qr_{i}.png")
```

For more advanced batch operations with styling:

```python
from betterqr import QR

urls = ["https://example1.com", "https://example2.com"]
colors = ["#FF6B6B", "#4ECDC4"]

for url, color in zip(urls, colors):
    qr = QR(url).style(fill_color=color)
    qr.save(f"qr_{color[1:]}.png")
```

## 5. Advanced Topics

### Error Correction Levels

QR codes support four error correction levels, allowing recovery from damaged or obscured codes:

| Level | Recovery | Use Case |
|-------|----------|----------|
| L | ~7% | General use, low risk |
| M | ~15% | Standard use, recommended |
| Q | ~25% | High-risk environments |
| H | ~30% | With logos or heavy styling |

Use higher error correction levels when embedding logos or applying heavy visual effects:

```python
from betterqr import QR

# For QR codes with logos
qr = QR("https://example.com", ecc="H").logo("logo.png")
qr.save("qr_with_logo.png")
```

### Transparent Backgrounds

Generate QR codes with transparent backgrounds (PNG format):

```python
from betterqr import QR

qr = QR("https://example.com").style(
    back_color="transparent"
)
qr.save("transparent_qr.png")
```

### Logo Sizing and Scannability

Guidelines for embedding logos while maintaining scannability:

**Logo Size Ratio:**
- 0.2 - Very conservative, maximum scannability
- 0.3 - Recommended balance (default)
- 0.4 - Maximum size, requires ECC level H
- >0.4 - Not recommended

**Best Practices:**
1. Always use ECC level H when embedding logos
2. Keep logo ratio between 0.2 and 0.3 for best results
3. Use square or rounded logo shapes for better integration
4. Test scannability with multiple QR code readers
5. Add padding around the logo to prevent overlap with QR data

Example of optimal logo embedding:

```python
from betterqr import QR

qr = QR(
    data="https://example.com",
    ecc="H"  # Use highest error correction
).logo(
    image_path="logo.png",
    ratio=0.3,  # Optimal ratio
    shape="rounded",
    padding=0.05
)
qr.save("optimized_qr.png")
```

## 6. Troubleshooting

### QR Code Not Scanning

**Problem:** Generated QR code won't scan properly

**Solutions:**
1. Increase error correction level: Use `ecc="H"` instead of `ecc="M"`
2. Reduce logo size: Set `logo_ratio` to 0.2 or 0.25
3. Increase box size: Use larger `box_size` values (15-20)
4. Use standard colors: Stick to black on white for maximum compatibility
5. Test with multiple readers: Try different QR code scanner apps

### Logo Not Appearing

**Problem:** Logo doesn't show in the QR code

**Solutions:**
1. Verify file path exists and is correct
2. Ensure image format is supported (PNG, JPG, GIF)
3. Check that ECC level is set to H: `ecc="H"`
4. Reduce logo ratio if it's too large
5. Ensure logo file is readable and not corrupted

### Animation Not Working

**Problem:** Animated GIF not generating correctly

**Solutions:**
1. Verify output filename ends with `.gif`
2. Check that `frames` parameter is set (minimum 2)
3. Ensure `fps` is reasonable (5-30 recommended)
4. Try reducing the number of frames
5. Check available disk space

### Memory Issues with Large Batches

**Problem:** Running out of memory when generating many QR codes

**Solutions:**
1. Generate QR codes in smaller batches
2. Delete QR objects after saving: `del qr`
3. Use garbage collection: `import gc; gc.collect()`
4. Reduce image size: Use smaller `box_size` values
5. Process files sequentially instead of loading all in memory

## 7. Contributing

We welcome contributions to BetterQR! Please see the [CONTRIBUTING.md](CONTRIBUTING.md) file for detailed guidelines on how to contribute.

## 8. License

BetterQR is released under the MIT License. See the LICENSE file for details.

---

**Last Updated:** 2026
**Version:** 1.0.0

