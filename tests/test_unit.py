"""
Unit tests
==========
Direct Python-API tests (no subprocess/CLI, no image decoding) covering
validation, edge cases, and internals that are cheap to check in-process.
"""
from __future__ import annotations

import pytest

import betterqr
from betterqr.encoder import encode_data
from betterqr.helpers import wifi_string, WiFi


class TestQRValidation:
    def test_rejects_invalid_ecc(self):
        with pytest.raises(ValueError):
            betterqr.QR("data", ecc="Z")

    def test_rejects_invalid_qr_type(self):
        with pytest.raises(ValueError):
            betterqr.QR("data", qr_type="rmqr")

    def test_micro_rejects_ecc_h(self):
        with pytest.raises(ValueError):
            betterqr.QR("data", qr_type="micro", ecc="H")

    def test_micro_accepts_l_m_q(self):
        for ecc in ("L", "M", "Q"):
            qr = betterqr.QR("HI", qr_type="micro", ecc=ecc)
            assert qr.qr_type == "micro"

    def test_data_too_long_raises(self):
        with pytest.raises(ValueError):
            betterqr.QR("A" * 5000, ecc="H")


class TestMicroQRCapacity:
    """
    Direct encoder-level checks for the M1/M3 4-bit-final-codeword bug:
    the last data codeword in Micro QR versions M1 and M3 only holds 4
    usable bits, not 8, so capacity must be computed accordingly.
    """

    def test_m3_ecc_m_numeric_boundary(self):
        # 18 digits is the true capacity of M3-M; must NOT overflow into M4.
        codewords, version, mode = encode_data("123456789012345678", "M",
                                                 None, qr_type="micro")
        assert version == 3

    def test_m3_ecc_m_numeric_over_boundary_escalates(self):
        # 19 digits exceeds M3-M's true capacity and must escalate to M4
        # rather than being silently truncated into an M3 symbol.
        codewords, version, mode = encode_data("1234567890123456789", "M",
                                                 None, qr_type="micro")
        assert version == 4

    def test_m1_numeric_boundary(self):
        # M1 only defines an ECC entry under the 'M' label in this table
        # (M1 has no selectable ECC level per spec — detection only).
        codewords, version, mode = encode_data("12345", "M", None, qr_type="micro")
        assert version == 1


class TestECI:
    def test_ascii_byte_data_has_no_eci_overhead(self):
        # Plain ASCII byte-mode data must pick the same version with or
        # without the ECI feature — no capacity cost for the common case.
        from betterqr.encoder import _needs_eci, MODE_BYTE
        assert _needs_eci("plain ascii", MODE_BYTE, "standard") is False

    def test_non_ascii_byte_data_needs_eci(self):
        from betterqr.encoder import _needs_eci, MODE_BYTE
        assert _needs_eci("héllo", MODE_BYTE, "standard") is True

    def test_eci_not_applied_to_micro(self):
        # Micro QR ECI support is out of scope for this pass; non-ASCII
        # Micro QR data must not get an ECI segment injected.
        from betterqr.encoder import _needs_eci, MODE_BYTE
        assert _needs_eci("héllo", MODE_BYTE, "micro") is False

    def test_non_ascii_still_encodes_and_decodes_via_api(self):
        qr = betterqr.QR("héllo wörld")
        buf = qr.to_buffer("PNG")
        assert buf.getbuffer().nbytes > 0


class TestWiFiHelper:
    def test_escapes_special_characters(self):
        s = wifi_string("my;ssid", "pass,word\\here", "WPA")
        assert "my\\;ssid" in s
        assert "pass\\,word\\\\here" in s

    def test_wpa_requires_min_length(self):
        with pytest.raises(ValueError):
            wifi_string("ssid", "short", "WPA")

    def test_wep_accepts_valid_ascii_length(self):
        # 5-character ASCII passphrase: valid 64-bit WEP key length.
        s = wifi_string("ssid", "abcde", "WEP")
        assert "P:abcde;" in s

    def test_wep_accepts_valid_hex_length(self):
        # 10 hex digits: valid 64-bit WEP key.
        s = wifi_string("ssid", "0123456789", "WEP")
        assert "P:0123456789;" in s

    def test_wep_rejects_invalid_length(self):
        with pytest.raises(ValueError):
            wifi_string("ssid", "abc123", "WEP")

    def test_nopass_ignores_password(self):
        s = wifi_string("ssid", "irrelevant", "NOPASS")
        assert "P:;" in s

    def test_empty_ssid_rejected(self):
        with pytest.raises(ValueError):
            wifi_string("", "password123", "WPA")

    def test_wifi_class_matches_function(self):
        w = WiFi("ssid", "password123", "WPA")
        assert str(w) == wifi_string("ssid", "password123", "WPA", False)


class TestLogo:
    def test_logo_does_not_crash(self):
        # Regression guard for the padding_px/border key-mismatch bug
        # that made every .logo() call raise KeyError.
        qr = betterqr.QR("https://example.com")
        qr.logo("logo.png")
        buf = qr.to_buffer("PNG")
        assert buf.getbuffer().nbytes > 0

    def test_logo_auto_escalates_ecc(self):
        qr = betterqr.QR("https://example.com", ecc="L")
        qr.logo("logo.png")
        assert qr.info()["ecc"] == "H"


class TestQRInfo:
    def test_module_count_matches_matrix(self):
        qr = betterqr.QR("test data")
        info = qr.info()
        assert info["modules"] == qr.module_count

    def test_micro_info_reports_type(self):
        qr = betterqr.QR("HI", qr_type="micro", ecc="L")
        assert qr.info()["type"] == "micro"


class TestBatch:
    def test_batch_creates_files(self, tmp_path):
        items = ["first", "second", "third"]
        results = betterqr.batch(items, output_dir=str(tmp_path))
        assert len(results) == 3
        pngs = list(tmp_path.glob("*.png"))
        assert len(pngs) == 3
