"""
report_to_discord.py
====================
Reads test_results.json (produced by the test suite) and the pytest
JSON report, then posts a detailed embed + QR zip to a Discord webhook.

Usage:
  python scripts/report_to_discord.py <webhook_url>
"""
from __future__ import annotations

import json
import os
import sys
import glob
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def _load_json(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def _build_embed(pytest_report: dict, qr_results: list[dict]) -> dict:
    stats = pytest_report.get("summary", {})
    total   = stats.get("total",   0)
    passed  = stats.get("passed",  0)
    failed  = stats.get("failed",  0)
    errors  = stats.get("error",   0)
    duration = round(pytest_report.get("duration", 0), 2)

    all_ok = (failed + errors) == 0
    color  = 0x2ECC71 if all_ok else 0xE74C3C
    status = "✅ All Passed" if all_ok else f"❌ {failed + errors} Failed"

    # ── per-QR breakdown ──────────────────────────────────────────────────────
    qr_lines: list[str] = []
    for r in qr_results:
        icon = "✅" if r["passed"] else "❌"
        name = r["test"]
        inp  = r["input"][:40] + ("…" if len(r["input"]) > 40 else "")
        dec  = r["decoded"][:40] + ("…" if len(r["decoded"]) > 40 else "")
        if r["passed"]:
            qr_lines.append(f"{icon} `{name}` → `{inp}`")
        else:
            qr_lines.append(
                f"{icon} `{name}`\n"
                f"    **Input:**   `{inp}`\n"
                f"    **Decoded:** `{dec}`"
            )

    # Discord field value cap: 1024 chars
    qr_text = "\n".join(qr_lines)
    if len(qr_text) > 1020:
        qr_text = qr_text[:1020] + "…"

    qr_passed = sum(1 for r in qr_results if r["passed"])
    qr_total  = len(qr_results)

    embed = {
        "title": "🚀 BetterQR CI/CD Report",
        "description": (
            "Automated end-to-end QR generation & decode verification for **BetterQR**.\n"
            "Every command is run, the output PNG is decoded, and the result is checked."
        ),
        "color": color,
        "fields": [
            {
                "name": "📊 Pytest Status",
                "value": status,
                "inline": True,
            },
            {
                "name": "⏱️ Duration",
                "value": f"{duration}s",
                "inline": True,
            },
            {
                "name": "🔬 Tests Run",
                "value": f"{passed}/{total} passed",
                "inline": True,
            },
            {
                "name": f"📷 QR Decode Results ({qr_passed}/{qr_total} OK)",
                "value": qr_text or "No QR results recorded.",
                "inline": False,
            },
        ],
        "footer": {"text": "BetterQR Automated Verification System"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return embed


def send(webhook_url: str) -> None:
    import urllib.request
    import urllib.parse

    pytest_path  = "report.json"
    results_path = "test_results.json"
    zip_path     = "qr_outputs.zip"

    if not os.path.exists(pytest_path):
        print(f"[discord] pytest report not found at {pytest_path}", file=sys.stderr)
        pytest_report: dict = {"summary": {}, "duration": 0}
    else:
        pytest_report = _load_json(pytest_path)

    qr_results: list[dict] = []
    if os.path.exists(results_path):
        qr_results = _load_json(results_path)

    embed = _build_embed(pytest_report, qr_results)

    # ── send with zip attachment ───────────────────────────────────────────────
    import requests  # noqa: F401  (available in CI)

    files: dict = {}
    payload: dict = {"embeds": [embed]}

    if os.path.exists(zip_path):
        files["file0"] = (
            "qr_outputs.zip",
            open(zip_path, "rb"),
            "application/zip",
        )

    try:
        if files:
            resp = requests.post(
                webhook_url,
                data={"payload_json": json.dumps(payload)},
                files=files,
            )
        else:
            resp = requests.post(webhook_url, json=payload)
        resp.raise_for_status()
        print(f"[discord] Report sent (status {resp.status_code}).")
    except Exception as exc:
        print(f"[discord] Failed to send: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        for f in files.values():
            f[1].close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/report_to_discord.py <webhook_url>")
        sys.exit(1)
    send(sys.argv[1])