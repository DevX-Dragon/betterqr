import json
import requests
import sys
import os
import glob
from datetime import datetime

def send_to_discord(webhook_url, report_path, image_dir="."):
    if not os.path.exists(report_path):
        print(f"Report file {report_path} not found.")
        return

    try:
        with open(report_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading report file: {e}")
        return

    stats = data.get('summary', {})
    total = stats.get('total', 0)
    passed = stats.get('passed', 0)
    failed = stats.get('failed', 0)
    duration = round(data.get('duration', 0), 2)

    color = 0x2ecc71 if failed == 0 else 0xe74c3c

    embed = {
        "title": "🚀 BetterQR CI/CD Report",
        "description": f"Automated test execution and verification for **BetterQR**.",
        "color": color,
        "fields": [
            {"name": "📊 Status", "value": "✅ All Passed" if failed == 0 else "❌ Failures Detected", "inline": True},
            {"name": "⏱️ Duration", "value": f"{duration}s", "inline": True},
            {"name": "📝 Tests", "value": f"{passed}/{total} passed", "inline": True},
        ],
        "footer": {"text": "BetterQR Automated Verification System"},
        "timestamp": datetime.utcnow().isoformat()
    }

    # Collect generated images - search in the current directory
    images = glob.glob("test_*.png")
    files = {}
    
    # Discord allows up to 10 files per message
    for i, img_path in enumerate(images[:10]):
        filename = os.path.basename(img_path)
        files[f"file{i}"] = (filename, open(img_path, 'rb'), 'image/png')

    payload = {
        "payload_json": json.dumps({"embeds": [embed]})
    }
    
    try:
        if files:
            response = requests.post(webhook_url, data=payload, files=files)
        else:
            response = requests.post(webhook_url, json={"embeds": [embed]})
            
        response.raise_for_status()
        print(f"Successfully sent report with {len(files)} images to Discord.")
    except Exception as e:
        print(f"Failed to send report to Discord: {e}")
    finally:
        for f in files.values():
            f[1].close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 report_to_discord.py <webhook_url> <report_json_path>")
        sys.exit(1)
    
    send_to_discord(sys.argv[1], sys.argv[2])
