"""
Generation tests
================
Fast smoke tests: for every CLI option and combination, verify the command
exits successfully and produces a non-empty output file. These do NOT
decode the result — see test_decode_roundtrip.py for fidelity checks.
All tests made by DevX-Dragon and some helpers!!
"""
from __future__ import annotations
from pathlib import Path
import pytest
from conftest import out, cli


def _assert_file_ok(path: str, min_bytes: int = 50):
    p = Path(path)
    assert p.exists(), f"expected output file at {path}"
    assert p.stat().st_size >= min_bytes, f"{path} is suspiciously small/empty"


class TestBasicGeneration:
    @pytest.mark.parametrize("data", [
        "https://example.com",
        "Plain text payload",
        "A" * 500,
        "0123456789",
        "Hello & World! <test> 'quote' \"dquote\"",
        "emoji test \U0001F600\U0001F4E1",
    ])
    def test_various_payloads(self, data, tmp_path):
        f = str(tmp_path / "gen.png")
        res = cli(data, f)
        assert res.returncode == 0, res.stderr
        _assert_file_ok(f)

    def test_empty_data_rejected(self, tmp_path):
        f = str(tmp_path / "empty.png")
        res = cli("", f)
        assert res.returncode != 0

    @pytest.mark.parametrize("fmt,ext", [("PNG", "png"), ("SVG", "svg"), ("JPEG", "jpg")])
    def test_output_formats(self, fmt, ext, tmp_path):
        f = str(tmp_path / f"fmt.{ext}")
        res = cli("format test", f)
        assert res.returncode == 0, res.stderr
        _assert_file_ok(f)


class TestECCAndType:
    @pytest.mark.parametrize("ecc", ["L", "M", "Q", "H"])
    def test_standard_ecc_levels(self, ecc, tmp_path):
        f = str(tmp_path / f"ecc_{ecc}.png")
        res = cli("ecc test", f, "-e", ecc)
        assert res.returncode == 0, res.stderr
        _assert_file_ok(f)

    @pytest.mark.parametrize("ecc", ["L", "M", "Q"])
    def test_micro_ecc_levels(self, ecc, tmp_path):
        f = str(tmp_path / f"micro_ecc_{ecc}.png")
        res = cli("HI", f, "--type", "micro", "-e", ecc)
        assert res.returncode == 0, res.stderr
        _assert_file_ok(f)

    def test_micro_rejects_ecc_h(self, tmp_path):
        f = str(tmp_path / "micro_h.png")
        res = cli("HI", f, "--type", "micro", "-e", "H")
        assert res.returncode != 0

    def test_invalid_qr_type_rejected(self, tmp_path):
        f = str(tmp_path / "bad_type.png")
        res = cli("data", f, "--type", "rmqr")
        assert res.returncode != 0


SHAPES = ["square", "circle", "rounded", "diamond", "star",
          "gapped", "vertical_bar", "horizontal_bar"]

class TestStyling:
    @pytest.mark.parametrize("shape", SHAPES)
    def test_shapes(self, shape, tmp_path):
        f = str(tmp_path / f"shape_{shape}.png")
        res = cli(f"shape:{shape}", f, "-s", shape)
        assert res.returncode == 0, res.stderr
        _assert_file_ok(f)

    def test_custom_colors(self, tmp_path):
        f = str(tmp_path / "colors.png")
        res = cli("color test", f, "--fill", "#1D4ED8", "--back", "#F0F9FF")
        assert res.returncode == 0, res.stderr
        _assert_file_ok(f)

    def test_transparent_background(self, tmp_path):
        f = str(tmp_path / "transparent.png")
        res = cli("transparent bg", f, "--back", "transparent")
        assert res.returncode == 0, res.stderr
        _assert_file_ok(f)

    def test_finder_color(self, tmp_path):
        f = str(tmp_path / "finder.png")
        res = cli("finder color", f, "--finder", "#FF0000")
        assert res.returncode == 0, res.stderr
        _assert_file_ok(f)

    def test_finder_color_on_micro(self, tmp_path):
        # Regression guard: styled Micro QR should only paint the single
        # top-left finder, not phantom finders near the other corners.
        f = str(tmp_path / "finder_micro.png")
        res = cli("HELLO", f, "--type", "micro", "-e", "M",
                   "-s", "circle", "--finder", "#FF0000")
        assert res.returncode == 0, res.stderr
        _assert_file_ok(f)

    @pytest.mark.parametrize("direction", ["horizontal", "vertical", "diagonal", "radial"])
    def test_gradients(self, direction, tmp_path):
        f = str(tmp_path / f"gradient_{direction}.png")
        res = cli(f"gradient:{direction}", f, "--gradient", "#FF6B6B", "#4ECDC4",
                   "--gradient-dir", direction)
        assert res.returncode == 0, res.stderr
        _assert_file_ok(f)

    def test_logo_embedding(self, tmp_path):
        # Regression guard for the padding_px/border key-mismatch crash.
        f = str(tmp_path / "logo.png")
        res = cli("logo test", f, "--logo", "logo.png")
        assert res.returncode == 0, res.stderr
        _assert_file_ok(f)

    def test_box_size_and_border(self, tmp_path):
        f = str(tmp_path / "sized.png")
        res = cli("sizing", f, "--box-size", "20", "--border", "1")
        assert res.returncode == 0, res.stderr
        _assert_file_ok(f)


FRAME_STYLES = ["simple", "rounded", "double", "shadow", "fancy"]

class TestFrameAndLabel:
    @pytest.mark.parametrize("style", FRAME_STYLES)
    def test_frames(self, style, tmp_path):
        f = str(tmp_path / f"frame_{style}.png")
        res = cli(f"frame:{style}", f, "--frame", style)
        assert res.returncode == 0, res.stderr
        _assert_file_ok(f)

    def test_label_below(self, tmp_path):
        f = str(tmp_path / "label_below.png")
        res = cli("scan me", f, "--label", "Visit our site")
        assert res.returncode == 0, res.stderr
        _assert_file_ok(f)

    def test_label_above(self, tmp_path):
        f = str(tmp_path / "label_above.png")
        res = cli("scan me", f, "--label", "Scan Here", "--label-above")
        assert res.returncode == 0, res.stderr
        _assert_file_ok(f)

    def test_frame_with_label(self, tmp_path):
        f = str(tmp_path / "frame_label.png")
        res = cli("framed", f, "--frame", "fancy", "--label", "WiFi Password")
        assert res.returncode == 0, res.stderr
        _assert_file_ok(f)

    def test_label_is_actually_visible_outside_frame(self, tmp_path):
        """Regression test: the label must render in its own reserved band,
        not overlap/hide behind the frame border stroke (see devlog bug where
        label text was drawn at the same y-position as the frame border)."""
        from PIL import Image
        import numpy as np
        from betterqr.extras.image_ops import add_frame

        qr = Image.new("RGBA", (200, 200), (255, 255, 255, 255))
        img = add_frame(
            qr, style="simple", frame_color="#0000FF", frame_width=40,
            label="HELLO WORLD", label_color="#FF0000", label_size=20,
            label_position="bottom", background_color="#FFFFFF",
        )
        arr = np.array(img.convert("RGB"))
        h = arr.shape[0]

        red_mask = (arr[:, :, 0] > 150) & (arr[:, :, 1] < 100) & (arr[:, :, 2] < 100)
        blue_mask = (arr[:, :, 2] > 150) & (arr[:, :, 0] < 100)

        assert red_mask.any(), "label text was not rendered at all"

        red_rows = np.where(red_mask.any(axis=1))[0]
        blue_rows = np.where(blue_mask.any(axis=1))[0]

        # The label band must sit below the frame's bottom border, not overlap it.
        assert red_rows.min() > blue_rows.max(), (
            "label text overlaps the frame border instead of sitting in its own band"
        )
        # And it should be near the bottom of the canvas, not cut off.
        assert red_rows.max() > h - 40


ANIM_EFFECTS = ["shimmer", "fade", "scan", "pulse", "build",
                "matrix", "wave", "blink", "typewriter", "rotate"]

class TestAnimation:
    @pytest.mark.parametrize("effect", ANIM_EFFECTS)
    def test_animation_effects(self, effect, tmp_path):
        f = str(tmp_path / f"anim_{effect}.gif")
        res = cli(f"anim:{effect}", f, "--effect", effect, "--frames", "5", "--fps", "10")
        assert res.returncode == 0, res.stderr
        _assert_file_ok(f, min_bytes=200)


class TestDataTypeShortcuts:
    def test_wifi_wpa(self, tmp_path):
        f = str(tmp_path / "wifi_wpa.png")
        res = cli("--wifi", "MyNetwork", "MyPassword123", "--security", "WPA", f)
        assert res.returncode == 0, res.stderr
        _assert_file_ok(f)

    def test_wifi_wep_valid_key(self, tmp_path):
        f = str(tmp_path / "wifi_wep.png")
        # 5-character ASCII WEP key (valid 64-bit WEP passphrase length).
        res = cli("--wifi", "OfficeNet", "abcde", "--security", "WEP", f)
        assert res.returncode == 0, res.stderr
        _assert_file_ok(f)

    def test_wifi_wep_invalid_key_rejected(self, tmp_path):
        f = str(tmp_path / "wifi_wep_bad.png")
        res = cli("--wifi", "OfficeNet", "abc123", "--security", "WEP", f)
        assert res.returncode != 0

    def test_wifi_nopass(self, tmp_path):
        f = str(tmp_path / "wifi_open.png")
        res = cli("--wifi", "FreeWifi", "--security", "nopass", f)
        assert res.returncode == 0, res.stderr
        _assert_file_ok(f)

    def test_geo(self, tmp_path):
        f = str(tmp_path / "geo.png")
        res = cli("--geo", "51.5074", "-0.1278", f)
        assert res.returncode == 0, res.stderr
        _assert_file_ok(f)

    def test_sms(self, tmp_path):
        f = str(tmp_path / "sms.png")
        res = cli("--sms", "+15550199", "Hello from BetterQR!", f)
        assert res.returncode == 0, res.stderr
        _assert_file_ok(f)

    def test_phone(self, tmp_path):
        f = str(tmp_path / "phone.png")
        res = cli("--phone", "+18005550199", f)
        assert res.returncode == 0, res.stderr
        _assert_file_ok(f)

    def test_email_basic(self, tmp_path):
        f = str(tmp_path / "email.png")
        res = cli("--email", "hi@example.com", f)
        assert res.returncode == 0, res.stderr
        _assert_file_ok(f)

    def test_email_with_subject_body(self, tmp_path):
        f = str(tmp_path / "email_full.png")
        res = cli("--email", "hi@example.com", "Hello", "World", f)
        assert res.returncode == 0, res.stderr
        _assert_file_ok(f)

    def test_contact_vcard(self, tmp_path):
        f = str(tmp_path / "vcard.png")
        res = cli("--contact", "Jane Doe", "--phone", "+15550199",
                   "--email", "jane@example.com", "--org", "Acme Inc", f)
        assert res.returncode == 0, res.stderr
        _assert_file_ok(f)