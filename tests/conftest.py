"""
Shared fixtures and helpers for the BetterQR test suite.

Decoding uses zxing-cpp rather than pyzbar/zbar: zbar has no support for
Micro QR at all (it returns zero results even for valid Micro QR images),
so it can't be used to verify a large part of this library's surface area.
zxing-cpp decodes standard QR and Micro QR equally well.
All tests made by DevX-Dragon and some helpers!
"""
from __future__ import annotations

import io
import json
import subprocess
import zipfile
from pathlib import Path

import pytest
from PIL import Image

import zxingcpp

try:
    import cairosvg
    HAVE_CAIROSVG = True
except ImportError:
    HAVE_CAIROSVG = False


OUTPUT_DIR = Path("qr_outputs")
RESULTS: list[dict] = []   # populated during the run; reported via scripts/report_to_discord.py


@pytest.fixture(scope="session", autouse=True)
def prepare_output_dir():
    OUTPUT_DIR.mkdir(exist_ok=True)
    yield
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


def record(test_name: str, input_string: str, expected: str,
           decoded: str | None, output_file: str) -> None:
    """Append a result record for the Discord report script."""
    passed = decoded is not None and (decoded == expected or expected in decoded)
    RESULTS.append({
        "test": test_name,
        "input": input_string,
        "expected_contains": expected,
        "decoded": decoded if decoded is not None else "<decode_failed>",
        "file": output_file,
        "passed": passed,
    })


def out(filename: str) -> str:
    """Return a path inside the shared output directory."""
    return str(OUTPUT_DIR / filename)


def cli(*args) -> subprocess.CompletedProcess:
    """Run the betterqr CLI and return the CompletedProcess."""
    return subprocess.run(
        ["betterqr", *[str(a) for a in args]],
        capture_output=True, text=True,
    )


def decode_image(image_path: str | Path) -> str | None:
    """Decode a PNG/JPG QR image; return the payload string or None."""
    path = Path(image_path)
    if not path.exists():
        return None
    try:
        img = Image.open(path).convert("RGB")
        results = zxingcpp.read_barcodes(img)
        return results[0].text if results else None
    except Exception:
        return None


def decode_svg(svg_path: str | Path, size: int = 600) -> str | None:
    """Rasterize an SVG QR code and decode it."""
    if not HAVE_CAIROSVG:
        pytest.skip("cairosvg not installed; can't rasterize SVG for decoding")
    path = Path(svg_path)
    if not path.exists():
        return None
    try:
        png_bytes = cairosvg.svg2png(
            url=str(path), output_width=size, output_height=size
        )
        img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
        results = zxingcpp.read_barcodes(img)
        return results[0].text if results else None
    except Exception:
        return None


def decode(path: str | Path) -> str | None:
    """Decode a QR image regardless of format (PNG/JPG/SVG)."""
    path = Path(path)
    if path.suffix.lower() == ".svg":
        return decode_svg(path)
    return decode_image(path)
