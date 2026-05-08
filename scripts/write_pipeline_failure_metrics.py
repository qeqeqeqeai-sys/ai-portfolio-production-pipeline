import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

import requests

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

RUN_DATE_SGT = datetime.now(ZoneInfo("Asia/Singapore")).date().isoformat()

if not SUPABASE_URL:
    raise RuntimeError("Missing SUPABASE_URL")

if not SUPABASE_KEY:
    raise RuntimeError("Missing SUPABASE_SERVICE_ROLE_KEY")


def read_last_error() -> str:
    log_dir = Path("logs")

    if not log_dir.exists():
        return "Workflow failed. No logs directory found."

    log_files = sorted(log_dir.glob("*.log"))

    if not log_files:
        return "Workflow failed. No log files found."

    combined = []

    for file in log_files:
        try:
            text = file.read_text(encoding="utf-8", errors="ignore")
            lines = text.strip().splitlines()
            tail = "\n".join(lines[-30:])
            combined.append(f"--- {file.name} ---\n{tail}")
        except Exception as exc:
            combined.append(f"Could not read {file.name}: {exc}")

    error_text = "\n\n".join(combined)

    return error_text[-3000:]


HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

payload = {
    "run_date_sgt": RUN_DATE_SGT,
    "status": "FAILED",

    "signal_rows": None,
    "portfolio_rows": None,
    "subsectors": None,
    "portfolio_subsectors": None,

    "cash_weight": None,
    "avg_alpha_score": None,
    "top_alpha_ticker": None,

    "github_run_id": os.getenv("GITHUB_RUN_ID"),
    "github_workflow": os.getenv("GITHUB_WORKFLOW"),
    "github_repository": os.getenv("GITHUB_REPOSITORY"),
    "github_branch": os.getenv("GITHUB_REF_NAME"),

    "error_message": read_last_error(),
}

url = f"{SUPABASE_URL}/rest/v1/production_pipeline_runs"

response = requests.post(
    url,
    headers=HEADERS,
    data=json.dumps(payload),
    timeout=60,
)

if response.status_code >= 400:
    raise RuntimeError(
        f"Failed to write failure metrics: "
        f"{response.status_code} - {response.text}"
    )

print("[DONE] Failure metrics written successfully.")