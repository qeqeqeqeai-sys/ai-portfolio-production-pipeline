#!/usr/bin/env python3

import os
import sys
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

SGT = ZoneInfo("Asia/Singapore")


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("Telegram secrets missing; skipping archival failure alert.")
        return 0

    pipeline = os.getenv("PIPELINE_NAME", "AI_PORTFOLIO_PRODUCTION")
    run_id = os.getenv("GITHUB_RUN_ID", "unknown")
    repo = os.getenv("GITHUB_REPOSITORY", "unknown")
    branch = os.getenv("GITHUB_REF_NAME", "unknown")
    status = os.getenv("PIPELINE_STATUS", "UNKNOWN")
    now = datetime.now(SGT).strftime("%Y-%m-%d %H:%M:%S SGT")

    message = (
        "⚠️ <b>ARCHIVAL FAILURE</b>\n"
        f"<b>Pipeline:</b> {pipeline}\n"
        f"<b>Status:</b> {status}\n"
        f"<b>Run ID:</b> {run_id}\n"
        f"<b>Repo:</b> {repo}\n"
        f"<b>Branch:</b> {branch}\n"
        f"<b>Time:</b> {now}\n\n"
        "Production pipeline may have completed, but persistent archival failed.\n"
        "Check GitHub Actions logs immediately."
    )

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    response = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=30,
    )

    if response.status_code >= 300:
        print(f"Telegram archival failure alert failed: {response.status_code} {response.text}")
        return 1

    print("Telegram archival failure alert sent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())