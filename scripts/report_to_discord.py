"""
report_to_discord.py
====================
Reads test_results.json (produced by the test suite) and the pytest
JSON report, then posts a series of Discord messages to avoid hitting
the 6000-character-per-request and 1024-char-per-field limits.

Message layout
--------------
  Message 1  — Summary embed (status, counts, duration) + qr_outputs.zip
  Message 2+ — One embed per "chunk" of QR results (≤25 fields each,
                field values kept under 1024 chars)

Usage:
  python scripts/report_to_discord.py <webhook_url>
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests


# ── Discord hard limits ───────────────────────────────────────────────────────
MAX_FIELDS_PER_EMBED = 25      # Discord API max
MAX_FIELD_VALUE      = 1024    # chars per field value
MAX_EMBEDS_PER_MSG   = 10      # embeds per webhook POST
RATE_LIMIT_PAUSE     = 1.0     # seconds between POSTs (be nice to the API)


# ── helpers ───────────────────────────────────────────────────────────────────

def _load_json(path: str) -> dict | list:
    with open(path) as f:
        return json.load(f)


def _trunc(text: str, limit: int = 40) -> str:
    return text[:limit] + "…" if len(text) > limit else text


def _failed_test_names(pytest_report: dict, limit: int = 15) -> list[str]:
    """
    Names of tests that actually failed/errored, straight from pytest's own
    per-test outcomes (report.json's "tests" list) — NOT from qr_results.

    This matters because qr_results only ever contains tests that call
    record() (the decode-roundtrip suite). A failure in test_unit.py,
    test_generation.py, or test_performance.py bumps the summary's failed
    count but would otherwise never show up anywhere in the report, making
    it look like "1 failed" with every itemized result still green.
    """
    names = [
        t["nodeid"] for t in pytest_report.get("tests", [])
        if t.get("outcome") in ("failed", "error")
    ]
    return names[:limit]


def _post(webhook_url: str, payload: dict, files: dict | None = None) -> None:
    """POST one request to the webhook; raises on HTTP error."""
    if files:
        resp = requests.post(
            webhook_url,
            data={"payload_json": json.dumps(payload)},
            files=files,
        )
    else:
        resp = requests.post(webhook_url, json=payload)
    resp.raise_for_status()
    print(f"  [discord] sent (HTTP {resp.status_code})")
    time.sleep(RATE_LIMIT_PAUSE)


# ── embed builders ────────────────────────────────────────────────────────────

def _summary_embed(pytest_report: dict, qr_results: list[dict]) -> dict:
    stats    = pytest_report.get("summary", {})
    total    = stats.get("total", stats.get("collected", 0))
    passed   = stats.get("passed", 0)
    failed   = stats.get("failed", 0)
    errors   = stats.get("error",  0)
    duration = round(pytest_report.get("duration", 0), 2)
    exitcode = pytest_report.get("exitcode")

    # pytest's own exit code is the ground truth. 0 = all collected tests
    # passed. Anything else — including "0 collected, 0 failed" — means the
    # run did NOT verify anything, and must never be reported as a pass.
    # (exitcode 4 = usage error / bad path, 5 = no tests collected.)
    nothing_ran = total == 0
    all_ok = (exitcode == 0) and (failed + errors == 0) and not nothing_ran

    if nothing_ran:
        color = 0xE74C3C
        status_val = f"⚠️ 0 tests ran (exitcode {exitcode})"
    elif all_ok:
        color = 0x2ECC71
        status_val = "✅ All Passed"
    else:
        color = 0xE74C3C
        status_val = f"❌ {failed + errors} Failed"

    qr_passed = sum(1 for r in qr_results if r["passed"])
    qr_total  = len(qr_results)
    if qr_total == 0:
        qr_status = "— no QR results recorded"
    elif qr_passed == qr_total:
        qr_status = "✅ All decoded OK"
    else:
        qr_status = f"⚠️ {qr_total - qr_passed} decode failure(s)"

    embed: dict = {
        "title": "🚀 BetterQR CI/CD Report",
        "description": (
            "Automated end-to-end QR generation & decode verification.\n"
            "Every CLI command is ran, the PNG decoded, and the result checked.\n"
            "Designed by DevX-Dragon"
        ),
        "color": color,
        "fields": [
            {"name": "📊 Pytest",       "value": status_val,                    "inline": True},
            {"name": "⏱️ Duration",     "value": f"{duration}s",                "inline": True},
            {"name": "🔬 Tests",        "value": f"{passed}/{total} passed",    "inline": True},
            {"name": "📷 QR Decodes",   "value": f"{qr_passed}/{qr_total} OK", "inline": True},
            {"name": "📦 Attachment",   "value": qr_status,                    "inline": True},
        ],
        "footer": {"text": "BetterQR Automated Verification System"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if nothing_ran:
        embed["fields"].append({
            "name": "🧨 Nothing was verified",
            "value": (
                "pytest collected **0 tests** (exitcode "
                f"`{exitcode}`). This usually means the test path was wrong, "
                "a plugin/dependency failed to install, or a `conftest.py` "
                "import blew up before collection. Check the raw CI log — "
                "this run proves nothing, despite looking green before this fix."
            ),
            "inline": False,
        })

    # A test can fail without ever touching qr_results (record() is only
    # called by the decode-roundtrip suite) — so name it explicitly here,
    # otherwise "❌ 1 Failed" shows up with no itemized entry anywhere below.
    if not all_ok and not nothing_ran:
        failed_names = _failed_test_names(pytest_report)
        if failed_names:
            value = "\n".join(f"`{_trunc(n, 90)}`" for n in failed_names)
            if len(value) > MAX_FIELD_VALUE:
                value = value[: MAX_FIELD_VALUE - 1] + "…"
            embed["fields"].append({"name": "🧨 Failed / errored tests", "value": value, "inline": False})
        else:
            embed["fields"].append({
                "name": "🧨 Failed / errored tests",
                "value": "(not reported by pytest-json-report — check the CI log)",
                "inline": False,
            })

    return embed


def _chunk_result_embeds(
    qr_results: list[dict],
    pytest_report: dict,
) -> list[dict]:
    """
    Return a list of embeds, each covering a slice of qr_results.
    One field per QR result; chunks of up to MAX_FIELDS_PER_EMBED.
    Returns [] when there's nothing to report, instead of one empty,
    pointless "QR Results — Part 1/1" embed.
    """
    if not qr_results:
        return []

    stats  = pytest_report.get("summary", {})
    failed = stats.get("failed", 0) + stats.get("error", 0)
    color  = 0x2ECC71 if failed == 0 else 0xE74C3C

    # Build one field per result
    fields: list[dict] = []
    for r in qr_results:
        icon = "✅" if r["passed"] else "❌"
        name = f"{icon} {r['test']}"

        inp = _trunc(r["input"],   50)
        dec = _trunc(r["decoded"], 50)

        if r["passed"]:
            value = f"`{inp}`"
        else:
            value = (
                f"**Input:**   `{inp}`\n"
                f"**Decoded:** `{dec}`"
            )

        # Ensure field value fits in Discord's limit
        if len(value) > MAX_FIELD_VALUE:
            value = value[: MAX_FIELD_VALUE - 1] + "…"

        fields.append({"name": name, "value": value, "inline": False})

    # Slice fields into embeds
    embeds: list[dict] = []
    total_chunks = (len(fields) + MAX_FIELDS_PER_EMBED - 1) // MAX_FIELDS_PER_EMBED or 1

    for chunk_idx, start in enumerate(range(0, max(len(fields), 1), MAX_FIELDS_PER_EMBED)):
        chunk = fields[start : start + MAX_FIELDS_PER_EMBED]
        embed: dict = {
            "title": f"📷 QR Results — Part {chunk_idx + 1}/{total_chunks}",
            "color": color,
            "fields": chunk,
        }
        if chunk_idx == total_chunks - 1:
            embed["footer"] = {"text": "BetterQR Automated Verification System"}
            embed["timestamp"] = datetime.now(timezone.utc).isoformat()
        embeds.append(embed)

    return embeds


# ── main send logic ───────────────────────────────────────────────────────────

def send(webhook_url: str) -> None:
    pytest_path  = "report.json"
    results_path = "test_results.json"
    zip_path     = "qr_outputs.zip"

    # Load data
    pytest_report: dict = (
        _load_json(pytest_path) if os.path.exists(pytest_path)
        else {"summary": {}, "duration": 0}
    )
    qr_results: list[dict] = (
        _load_json(results_path) if os.path.exists(results_path) else []  # type: ignore[assignment]
    )

    summary_embed  = _summary_embed(pytest_report, qr_results)
    result_embeds  = _chunk_result_embeds(qr_results, pytest_report)

    # ── Message 1: summary + zip attachment ───────────────────────────────────
    print("[discord] Sending summary message…")
    files: dict = {}
    if os.path.exists(zip_path):
        files["file0"] = ("qr_outputs.zip", open(zip_path, "rb"), "application/zip")

    try:
        _post(
            webhook_url,
            payload={"embeds": [summary_embed]},
            files=files or None,
        )
    finally:
        for fv in files.values():
            fv[1].close()

    # ── Messages 2+: result embeds, batched MAX_EMBEDS_PER_MSG at a time ──────
    for batch_start in range(0, len(result_embeds), MAX_EMBEDS_PER_MSG):
        batch = result_embeds[batch_start : batch_start + MAX_EMBEDS_PER_MSG]
        print(f"[discord] Sending result embeds {batch_start + 1}–{batch_start + len(batch)}…")
        _post(webhook_url, payload={"embeds": batch})

    print("[discord] All messages sent successfully.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/report_to_discord.py <webhook_url>")
        sys.exit(1)
    send(sys.argv[1])