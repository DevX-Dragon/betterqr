import subprocess
import os
import pytest
from PIL import Image
from pyzbar.pyzbar import decode
import shutil

# Helper to run CLI commands
def run_cli(args):
    result = subprocess.run(["betterqr"] + args, capture_output=True, text=True)
    return result

def decode_qr(image_path):
    if not os.path.exists(image_path):
        print(f"File not found: {image_path}")
        return None
    try:
        img = Image.open(image_path)
        decoded_objects = decode(img)
        if not decoded_objects:
            print(f"Could not decode QR from {image_path}")
            return None
        return decoded_objects[0].data.decode('utf-8')
    except Exception as e:
        print(f"Error decoding {image_path}: {e}")
        return None

@pytest.fixture(autouse=True)
def cleanup_files():
    if os.path.exists("qr.png"):
        os.remove("qr.png")
    yield

def test_basic_usage_verification():
    data = "https://example.com"
    output = "test_basic.png"
    res = run_cli([data, output])
    assert res.returncode == 0
    decoded = decode_qr(output)
    assert decoded == data

def test_custom_text_verification():
    data = "BetterQR is awesome"
    output = "test_text.png"
    res = run_cli([data, output])
    assert res.returncode == 0
    decoded = decode_qr(output)
    assert decoded == data

def test_wifi_verification():
    res = run_cli(["--wifi", "MyNet", "MyPassword123", "--security", "WPA"])
    assert res.returncode == 0
    assert os.path.exists("qr.png")
    decoded = decode_qr("qr.png")
    assert decoded is not None
    assert "MyNet" in decoded
    shutil.move("qr.png", "test_wifi.png")

def test_geo_verification():
    res = run_cli(["--geo", "51.5074", "-0.1278"])
    assert res.returncode == 0
    assert os.path.exists("qr.png")
    decoded = decode_qr("qr.png")
    assert decoded is not None
    assert "51.5074" in decoded
    shutil.move("qr.png", "test_geo.png")

def test_sms_verification():
    res = run_cli(["--sms", "+15550199", "Hello!"])
    assert res.returncode == 0
    assert os.path.exists("qr.png")
    decoded = decode_qr("qr.png")
    assert decoded is not None
    assert "15550199" in decoded
    shutil.move("qr.png", "test_sms.png")

def test_phone_verification():
    res = run_cli(["--phone", "+18005550199"])
    assert res.returncode == 0
    assert os.path.exists("qr.png")
    decoded = decode_qr("qr.png")
    assert decoded is not None
    assert "18005550199" in decoded
    shutil.move("qr.png", "test_phone.png")

def test_shapes_verification():
    data = "Shape Test"
    for shape in ["square", "rounded"]:
        out = f"test_shape_{shape}.png"
        res = run_cli([data, out, "-s", shape])
        assert res.returncode == 0
        decoded = decode_qr(out)
        assert decoded == data

def test_gradient_verification():
    data = "Gradient Test"
    out = "test_gradient.png"
    res = run_cli([data, out, "--gradient", "#000000", "#333333"])
    assert res.returncode == 0
    decoded = decode_qr(out)
    assert decoded == data
