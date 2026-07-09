"""
Decode round-trip tests
========================
Generate a QR code, decode it with zxing-cpp, and assert the payload
matches. This is the suite that actually catches encoding bugs (a file
existing doesn't mean it scans correctly) — it's how the Micro QR
capacity-miscalculation bug was originally caught.
"""
from __future__ import annotations

import pytest

from conftest import out, cli, decode, record


class TestBasicRoundTrip:
    @pytest.mark.parametrize("data", [
        "https://example.com",
        "BetterQR is awesome!",
        "A" * 200,
        "0123456789",
        "Hello & World! <test>",
    ])
    def test_png_roundtrip(self, data):
        f = out(f"rt_{abs(hash(data))}.png")
        res = cli(data, f)
        assert res.returncode == 0, res.stderr
        decoded = decode(f)
        record("png_roundtrip", data, data, decoded, f)
        assert decoded == data

    def test_svg_roundtrip(self):
        data = "https://example.com/svg"
        f = out("basic.svg")
        res = cli(data, f)
        assert res.returncode == 0, res.stderr
        decoded = decode(f)
        record("svg_roundtrip", data, data, decoded, f)
        assert decoded == data

    @pytest.mark.parametrize("data", [
        "héllo wörld ünïcödé",
        "日本語テスト",
        "emoji test \U0001F389\U0001F525",
    ])
    def test_non_ascii_roundtrip(self, data):
        # Non-ASCII byte-mode data is declared via an ECI segment so
        # compliant decoders interpret it as UTF-8 rather than the
        # ISO-8859-1 default.
        f = out(f"unicode_{abs(hash(data))}.png")
        res = cli(data, f)
        assert res.returncode == 0, res.stderr
        decoded = decode(f)
        record("non_ascii_roundtrip", data, data, decoded, f)
        assert decoded == data


class TestECCRoundTrip:
    @pytest.mark.parametrize("ecc", ["L", "M", "Q", "H"])
    def test_standard_ecc(self, ecc):
        data = "ECC-test-data"
        f = out(f"ecc_{ecc}.png")
        res = cli(data, f, "-e", ecc)
        assert res.returncode == 0, res.stderr
        decoded = decode(f)
        record(f"ecc_{ecc}", data, data, decoded, f)
        assert decoded == data


class TestMicroQRRoundTrip:
    """
    Micro QR gets its own dedicated round-trip coverage, including cases
    right at each symbol's capacity boundary — this is exactly where the
    M1/M3 4-bit-final-codeword bug produced silently-corrupted symbols.
    """

    @pytest.mark.parametrize("data,ecc", [
        ("HI", "L"),
        ("HELLO", "M"),
        ("1234567890123456789", "M"),   # 19 digits: exceeds M3-M, escalates to M4
        ("123456789012345678901234567890", "M"),  # 30 digits: exact M4-M capacity
        ("ABCDEFGHIJK", "L"),           # 11 chars: exact M3-L alphanumeric capacity
    ])
    def test_micro_capacity_boundaries(self, data, ecc):
        f = out(f"micro_{abs(hash((data, ecc)))}.png")
        res = cli(data, f, "--type", "micro", "-e", ecc)
        assert res.returncode == 0, res.stderr
        decoded = decode(f)
        record(f"micro_boundary_{ecc}", data, data, decoded, f)
        assert decoded == data

    def test_micro_svg_roundtrip(self):
        data = "MICROSVG"
        f = out("micro.svg")
        res = cli(data, f, "--type", "micro", "-e", "M")
        assert res.returncode == 0, res.stderr
        decoded = decode(f)
        record("micro_svg", data, data, decoded, f)
        assert decoded == data

    def test_micro_over_capacity_escalates_or_rejects(self):
        # 21 digits at ECC-M should NOT fit in M3 (19-digit max) and must
        # either escalate to M4 (and still decode correctly) or be
        # rejected outright — it must never silently truncate.
        data = "123456789012345678901"  # 21 digits
        f = out("micro_escalate.png")
        res = cli(data, f, "--type", "micro", "-e", "M")
        if res.returncode == 0:
            decoded = decode(f)
            record("micro_escalate", data, data, decoded, f)
            assert decoded == data
        else:
            record("micro_escalate_rejected", data, data, None, f)


class TestStyledRoundTrip:
    @pytest.mark.parametrize("shape", ["square", "circle", "rounded", "diamond",
                                        "star", "gapped", "vertical_bar", "horizontal_bar"])
    def test_shapes(self, shape):
        data = f"shape:{shape}"
        f = out(f"shape_{shape}.png")
        res = cli(data, f, "-s", shape)
        assert res.returncode == 0, res.stderr
        decoded = decode(f)
        record(f"shape_{shape}", data, data, decoded, f)
        assert decoded == data

    def test_finder_color_on_micro_still_scans(self):
        # Regression guard for the finder-detection/qr_type bug: styled
        # Micro QR must still decode correctly even with a custom finder
        # color and non-square module shape.
        data = "MICROSTYLE"
        f = out("micro_styled.png")
        res = cli(data, f, "--type", "micro", "-e", "M",
                   "-s", "circle", "--finder", "#FF0000")
        assert res.returncode == 0, res.stderr
        decoded = decode(f)
        record("micro_styled_finder", data, data, decoded, f)
        assert decoded == data

    def test_gradient(self):
        data = "gradient:diagonal"
        f = out("gradient.png")
        res = cli(data, f, "--gradient", "#FF6B6B", "#4ECDC4", "--gradient-dir", "diagonal")
        assert res.returncode == 0, res.stderr
        decoded = decode(f)
        record("gradient", data, data, decoded, f)
        assert decoded == data

    def test_logo_still_scans(self):
        # Regression guard: ECC is auto-escalated to H when a logo is
        # embedded, so the code should survive the logo cutout.
        data = "https://example.com/logo"
        f = out("logo_roundtrip.png")
        res = cli(data, f, "--logo", "logo.png")
        assert res.returncode == 0, res.stderr
        decoded = decode(f)
        record("logo_roundtrip", data, data, decoded, f)
        assert decoded == data

    def test_frame_and_label_still_scans(self):
        data = "framed and labelled"
        f = out("frame_roundtrip.png")
        res = cli(data, f, "--frame", "fancy", "--label", "Scan me")
        assert res.returncode == 0, res.stderr
        decoded = decode(f)
        record("frame_roundtrip", data, data, decoded, f)
        assert decoded == data


class TestDataTypeRoundTrip:
    def test_wifi_wpa(self):
        ssid, password = "MyNetwork", "MyPassword123"
        f = out("wifi_wpa.png")
        res = cli("--wifi", ssid, password, "--security", "WPA", f)
        assert res.returncode == 0, res.stderr
        decoded = decode(f)
        record("wifi_wpa", f"WIFI:{ssid}/{password}", ssid, decoded, f)
        assert decoded is not None and ssid in decoded

    def test_wifi_special_characters_are_escaped(self):
        # Regression guard: SSID/password containing WIFI: control
        # characters (';', ',', '\\') must be escaped, not passed through
        # raw (which previously produced malformed/misparsed strings).
        ssid, password = "office;net", "pass;word,here"
        f = out("wifi_escaped.png")
        res = cli("--wifi", ssid, password, "--security", "WPA", f)
        assert res.returncode == 0, res.stderr
        decoded = decode(f)
        record("wifi_escaped", ssid, "S:office\\;net", decoded, f)
        assert decoded is not None
        assert "S:office\\;net" in decoded
        assert "P:pass\\;word\\,here" in decoded

    def test_wifi_nopass(self):
        ssid = "FreeWifi"
        f = out("wifi_nopass.png")
        res = cli("--wifi", ssid, "--security", "nopass", f)
        assert res.returncode == 0, res.stderr
        decoded = decode(f)
        record("wifi_nopass", f"WIFI:{ssid}", ssid, decoded, f)
        assert decoded is not None and ssid in decoded

    def test_geo(self):
        lat, lon = "51.5074", "-0.1278"
        f = out("geo.png")
        res = cli("--geo", lat, lon, f)
        assert res.returncode == 0, res.stderr
        decoded = decode(f)
        record("geo", f"geo:{lat},{lon}", lat, decoded, f)
        assert decoded is not None and lat in decoded

    def test_sms(self):
        phone, msg = "+15550199", "Hello from BetterQR!"
        f = out("sms.png")
        res = cli("--sms", phone, msg, f)
        assert res.returncode == 0, res.stderr
        decoded = decode(f)
        record("sms", f"sms:{phone}:{msg}", phone.lstrip("+"), decoded, f)
        assert decoded is not None and "5550199" in decoded

    def test_phone(self):
        number = "+18005550199"
        f = out("phone.png")
        res = cli("--phone", number, f)
        assert res.returncode == 0, res.stderr
        decoded = decode(f)
        record("phone", f"tel:{number}", "18005550199", decoded, f)
        assert decoded is not None and "18005550199" in decoded

    def test_email_basic(self):
        address = "hi@example.com"
        f = out("email_basic.png")
        res = cli("--email", address, f)
        assert res.returncode == 0, res.stderr
        decoded = decode(f)
        record("email_basic", f"mailto:{address}", address, decoded, f)
        assert decoded is not None and address in decoded

    def test_email_with_subject_body(self):
        address, subject, body = "hi@example.com", "Hello", "World"
        f = out("email_full.png")
        res = cli("--email", address, subject, body, f)
        assert res.returncode == 0, res.stderr
        decoded = decode(f)
        record("email_full", f"mailto:{address}?subject={subject}", address, decoded, f)
        assert decoded is not None and address in decoded

    def test_contact_vcard(self):
        f = out("contact_vcard.png")
        res = cli("--contact", "Jane Doe", "--phone", "+15550199",
                   "--email", "jane@example.com", "--org", "Acme Inc", f)
        assert res.returncode == 0, res.stderr
        decoded = decode(f)
        record("contact_vcard", "vCard:Jane Doe/+15550199", "Jane Doe", decoded, f)
        assert decoded is not None and "Jane Doe" in decoded
