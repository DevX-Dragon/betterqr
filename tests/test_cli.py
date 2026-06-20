"""
BetterQR Comprehensive Test Suite
===================================
Tests all possible CLI commands, decodes generated QR codes,
and verifies the encoded data matches the original input.
"""
import subprocess
import os
import sys
import json
import shutil
import zipfile
import tempfile
from pathlib import Path
from datetime import datetime

import pytest
from PIL import Image
from pyzbar.pyzbar import decode as pyzbar_decode

# ── helpers ──────────────────────────────────────────────────────────────────

OUTPUT_DIR = Path("qr_outputs")
RESULTS: list[dict] = []          # populated during test run

def _cli(*args):
    """Run betterqr CLI and return CompletedProcess."""
    return subprocess.run(
        ["betterqr", *[str(a) for a in args]],
        capture_output=True, text=True
    )

def _decode(image_path: str | Path) -> str | None:
    """Decode a QR image; return data string or None."""
    path = Path(image_path)
    if not path.exists():
        return None
    try:
        img = Image.open(path).convert("RGB")
        objs = pyzbar_decode(img)
        return objs[0].data.decode("utf-8") if objs else None
    except Exception:
        return None

def _record(test_name: str, input_string: str, expected: str,
            decoded: str | None, output_file: str) -> None:
    """Append a result record for the final Discord report."""
    passed = decoded is not None and (
        decoded == expected or expected in decoded
    )
    RESULTS.append({
        "test": test_name,
        "input": input_string,
        "expected_contains": expected,
        "decoded": decoded if decoded is not None else "<decode_failed>",
        "file": output_file,
        "passed": passed,
    })

def out(filename: str) -> str:
    """Return a path inside OUTPUT_DIR."""
    return str(OUTPUT_DIR / filename)


# ── session setup ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def prepare_output_dir():
    OUTPUT_DIR.mkdir(exist_ok=True)
    yield
    # After all tests: write results JSON and create zip
    results_path = "test_results.json"
    with open(results_path, "w") as f:
        json.dump(RESULTS, f, indent=2)

    zip_path = "qr_outputs.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for img in OUTPUT_DIR.glob("*.png"):
            zf.write(img, img.name)
        for img in OUTPUT_DIR.glob("*.svg"):
            zf.write(img, img.name)
        # skip .gif — too large for Discord embed
    print(f"\n✓ Results written to {results_path}")
    print(f"✓ QR images zipped to {zip_path}")


# ── basic data ────────────────────────────────────────────────────────────────

class TestBasicData:
    def test_plain_url(self):
        data = "https://example.com"
        f = out("basic_url.png")
        res = _cli(data, f)
        assert res.returncode == 0, res.stderr
        decoded = _decode(f)
        _record("plain_url", data, data, decoded, f)
        assert decoded == data

    def test_plain_text(self):
        data = "BetterQR is awesome!"
        f = out("plain_text.png")
        res = _cli(data, f)
        assert res.returncode == 0, res.stderr
        decoded = _decode(f)
        _record("plain_text", data, data, decoded, f)
        assert decoded == data

    def test_long_text(self):
        data = "A" * 200
        f = out("long_text.png")
        res = _cli(data, f)
        assert res.returncode == 0, res.stderr
        decoded = _decode(f)
        _record("long_text", data, data, decoded, f)
        assert decoded == data

    def test_numeric_data(self):
        data = "0123456789"
        f = out("numeric.png")
        res = _cli(data, f)
        assert res.returncode == 0, res.stderr
        decoded = _decode(f)
        _record("numeric_data", data, data, decoded, f)
        assert decoded == data

    def test_svg_output(self):
        data = "https://example.com/svg"
        f = out("basic.svg")
        res = _cli(data, f)
        assert res.returncode == 0, res.stderr
        # SVG can't be decoded by pyzbar; just verify file was created
        assert Path(f).exists()
        _record("svg_output", data, data, "<svg_no_decode>", f)

    def test_special_chars(self):
        data = "Hello & World! <test>"
        f = out("special_chars.png")
        res = _cli(data, f)
        assert res.returncode == 0, res.stderr
        decoded = _decode(f)
        _record("special_chars", data, data, decoded, f)
        assert decoded == data


# ── ECC levels ────────────────────────────────────────────────────────────────

class TestECCLevels:
    @pytest.mark.parametrize("ecc", ["L", "M", "Q", "H"])
    def test_ecc(self, ecc):
        data = "ECC-test-data"
        f = out(f"ecc_{ecc}.png")
        res = _cli(data, f, "-e", ecc)
        assert res.returncode == 0, res.stderr
        decoded = _decode(f)
        _record(f"ecc_{ecc}", data, data, decoded, f)
        assert decoded == data


# ── QR type ───────────────────────────────────────────────────────────────────

class TestQRType:
    def test_standard(self):
        data = "standard"
        f = out("type_standard.png")
        res = _cli(data, f, "--type", "standard")
        assert res.returncode == 0, res.stderr
        decoded = _decode(f)
        _record("type_standard", data, data, decoded, f)
        assert decoded == data

    def test_micro(self):
        data = "HI"              # Micro QR has tiny capacity
        f = out("type_micro.png")
        res = _cli(data, f, "--type", "micro", "-e", "L")
        assert res.returncode == 0, res.stderr
        decoded = _decode(f)
        _record("type_micro", data, data, decoded, f)
        assert decoded == data


# ── shapes ────────────────────────────────────────────────────────────────────

SHAPES = ["square", "circle", "rounded", "diamond", "star",
          "gapped", "vertical_bar", "horizontal_bar"]

class TestShapes:
    @pytest.mark.parametrize("shape", SHAPES)
    def test_shape(self, shape):
        data = f"shape:{shape}"
        f = out(f"shape_{shape}.png")
        res = _cli(data, f, "-s", shape)
        assert res.returncode == 0, res.stderr
        decoded = _decode(f)
        _record(f"shape_{shape}", data, data, decoded, f)
        assert decoded == data


# ── colors ────────────────────────────────────────────────────────────────────

class TestColors:
    def test_custom_fill_and_back(self):
        data = "color test"
        f = out("color_custom.png")
        res = _cli(data, f, "--fill", "#1D4ED8", "--back", "#F0F9FF")
        assert res.returncode == 0, res.stderr
        decoded = _decode(f)
        _record("color_custom", data, data, decoded, f)
        assert decoded == data

    def test_transparent_back(self):
        data = "transparent bg"
        f = out("color_transparent.png")
        res = _cli(data, f, "--back", "transparent")
        assert res.returncode == 0, res.stderr
        decoded = _decode(f)
        _record("color_transparent", data, data, decoded, f)
        assert decoded == data

    def test_finder_color(self):
        data = "finder color"
        f = out("color_finder.png")
        res = _cli(data, f, "--finder", "#FF0000")
        assert res.returncode == 0, res.stderr
        decoded = _decode(f)
        _record("color_finder", data, data, decoded, f)
        assert decoded == data


# ── gradient ──────────────────────────────────────────────────────────────────

GRADIENT_DIRS = ["horizontal", "vertical", "diagonal", "radial"]

class TestGradients:
    @pytest.mark.parametrize("direction", GRADIENT_DIRS)
    def test_gradient(self, direction):
        data = f"gradient:{direction}"
        f = out(f"gradient_{direction}.png")
        res = _cli(data, f, "--gradient", "#FF6B6B", "#4ECDC4",
                   "--gradient-dir", direction)
        assert res.returncode == 0, res.stderr
        decoded = _decode(f)
        _record(f"gradient_{direction}", data, data, decoded, f)
        assert decoded == data


# ── frame & label ─────────────────────────────────────────────────────────────

FRAME_STYLES = ["simple", "rounded", "double", "shadow", "fancy"]

class TestFrameAndLabel:
    @pytest.mark.parametrize("style", FRAME_STYLES)
    def test_frame(self, style):
        data = f"frame:{style}"
        f = out(f"frame_{style}.png")
        res = _cli(data, f, "--frame", style)
        assert res.returncode == 0, res.stderr
        decoded = _decode(f)
        _record(f"frame_{style}", data, data, decoded, f)
        assert decoded == data

    def test_label_below(self):
        data = "scan me"
        f = out("label_below.png")
        res = _cli(data, f, "--label", "Visit our site")
        assert res.returncode == 0, res.stderr
        decoded = _decode(f)
        _record("label_below", data, data, decoded, f)
        assert decoded == data

    def test_label_above(self):
        data = "scan me"
        f = out("label_above.png")
        res = _cli(data, f, "--label", "Scan Here", "--label-above")
        assert res.returncode == 0, res.stderr
        decoded = _decode(f)
        _record("label_above", data, data, decoded, f)
        assert decoded == data

    def test_frame_with_label(self):
        data = "framed and labelled"
        f = out("frame_with_label.png")
        res = _cli(data, f, "--frame", "fancy", "--label", "WiFi Password")
        assert res.returncode == 0, res.stderr
        decoded = _decode(f)
        _record("frame_with_label", data, data, decoded, f)
        assert decoded == data


# ── data type shortcuts ───────────────────────────────────────────────────────

class TestDataTypes:
    def test_wifi_wpa(self):
        ssid, password = "MyNetwork", "MyPassword123"
        f = out("wifi_wpa.png")
        res = _cli("--wifi", ssid, password, "--security", "WPA", f)
        assert res.returncode == 0, res.stderr
        decoded = _decode(f)
        _record("wifi_wpa", f"WIFI:{ssid}/{password}", ssid, decoded, f)
        assert decoded is not None and ssid in decoded

    def test_wifi_wep(self):
        ssid, password = "OfficeNet", "abc123"
        f = out("wifi_wep.png")
        res = _cli("--wifi", ssid, password, "--security", "WEP", f)
        assert res.returncode == 0, res.stderr
        decoded = _decode(f)
        _record("wifi_wep", f"WIFI:{ssid}/{password}", ssid, decoded, f)
        assert decoded is not None and ssid in decoded

    def test_wifi_nopass(self):
        ssid = "FreeWifi"
        f = out("wifi_nopass.png")
        res = _cli("--wifi", ssid, "--security", "nopass", f)
        assert res.returncode == 0, res.stderr
        decoded = _decode(f)
        _record("wifi_nopass", f"WIFI:{ssid}", ssid, decoded, f)
        assert decoded is not None and ssid in decoded

    def test_geo(self):
        lat, lon = "51.5074", "-0.1278"
        f = out("geo.png")
        res = _cli("--geo", lat, lon, f)
        assert res.returncode == 0, res.stderr
        decoded = _decode(f)
        _record("geo", f"geo:{lat},{lon}", lat, decoded, f)
        assert decoded is not None and lat in decoded

    def test_sms(self):
        phone, msg = "+15550199", "Hello from BetterQR!"
        f = out("sms.png")
        res = _cli("--sms", phone, msg, f)
        assert res.returncode == 0, res.stderr
        decoded = _decode(f)
        _record("sms", f"sms:{phone}:{msg}", phone.lstrip("+"), decoded, f)
        assert decoded is not None and "5550199" in decoded

    def test_phone(self):
        number = "+18005550199"
        f = out("phone.png")
        res = _cli("--phone", number, f)
        assert res.returncode == 0, res.stderr
        decoded = _decode(f)
        _record("phone", f"tel:{number}", "18005550199", decoded, f)
        assert decoded is not None and "18005550199" in decoded

    def test_email_basic(self):
        address = "hi@example.com"
        f = out("email_basic.png")
        res = _cli("--email", address, f)
        assert res.returncode == 0, res.stderr
        decoded = _decode(f)
        _record("email_basic", f"mailto:{address}", address, decoded, f)
        assert decoded is not None and address in decoded

    def test_email_with_subject_body(self):
        address, subject, body = "hi@example.com", "Hello", "World"
        f = out("email_full.png")
        res = _cli("--email", address, subject, body, f)
        assert res.returncode == 0, res.stderr
        decoded = _decode(f)
        _record("email_full", f"mailto:{address}?subject={subject}", address, decoded, f)
        assert decoded is not None and address in decoded

    def test_contact_vcard(self):
        f = out("contact_vcard.png")
        res = _cli("--contact", "Jane Doe",
                   "--phone", "+15550199",
                   "--email", "jane@example.com",
                   "--org", "Acme Inc",
                   f)
        assert res.returncode == 0, res.stderr
        decoded = _decode(f)
        _record("contact_vcard", "vCard:Jane Doe/+15550199", "Jane Doe", decoded, f)
        assert decoded is not None and "Jane Doe" in decoded


# ── animation ─────────────────────────────────────────────────────────────────

ANIM_EFFECTS = ["shimmer", "fade", "scan", "pulse", "build",
                "matrix", "wave", "blink", "typewriter", "rotate"]

class TestAnimations:
    @pytest.mark.parametrize("effect", ANIM_EFFECTS)
    def test_animation(self, effect):
        data = f"anim:{effect}"
        f = out(f"anim_{effect}.gif")
        res = _cli(data, f, "--effect", effect, "--frames", "5", "--fps", "10")
        assert res.returncode == 0, res.stderr
        # GIFs can't be pyzbar-decoded; just verify creation
        assert Path(f).exists(), f"GIF not created for effect={effect}"
        _record(f"anim_{effect}", data, data, "<gif_no_decode>", str(f))


# ── box-size & border ─────────────────────────────────────────────────────────

class TestRenderOptions:
    def test_large_box_size(self):
        data = "big modules"
        f = out("big_box.png")
        res = _cli(data, f, "--box-size", "20")
        assert res.returncode == 0, res.stderr
        decoded = _decode(f)
        _record("large_box_size", data, data, decoded, f)
        assert decoded == data

    def test_small_border(self):
        data = "small border"
        f = out("small_border.png")
        res = _cli(data, f, "--border", "1")
        assert res.returncode == 0, res.stderr
        decoded = _decode(f)
        _record("small_border", data, data, decoded, f)
        assert decoded == data