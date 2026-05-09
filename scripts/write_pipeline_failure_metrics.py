import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

import requests


# =============================================================================
# Configuration
# =============================================================================

SGT = ZoneInfo("Asia/Singapore")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

RUN_DATE_SGT = datetime.now(SGT).date().isoformat()

LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))

TABLE_NAME = "production_pipeline_runs"

MAX_ERROR_CHARS = 3000


# =============================================================================
# Helpers
# =============================================================================

def log(message: str) -> None:
    now = datetime.now(SGT).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now} SGT] {message}", flush=True)


def require_env() -> None:
    missing = []

    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")

    if not SUPABASE_KEY:
        missing.append("SUPABASE_SERVICE_ROLE_KEY")

    if missing:
        raise RuntimeError(f"Missing required environment variables: {missing}")


def safe_float(value, default=None):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def read_recent_logs() -> str:
    if not LOG_DIR.exists():
        return "Workflow failed. No logs directory found."

    log_files = sorted(LOG_DIR.glob("*.log"))

    if not log_files:
        return "Workflow failed. No log files found."

    chunks = []

    for file in log_files:
        try:
            text = file.read_text(encoding="utf-8", errors="ignore")
            lines = text.strip().splitlines()
            tail = "\n".join(lines[-40:])

            chunks.append(
                f"--- {file.name} ---\n{tail}"
            )

        except Exception as exc:
            chunks.append(
                f"--- {file.name} ---\nCould not read log file: {exc}"
            )

    error_text = "\n\n".join(chunks).strip()

    if not error_text:
        return "Workflow failed. Logs were empty."

    return error_text[-MAX_ERROR_CHARS:]


def post_to_supabase(payload: dict) -> None:
    url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        url,
        headers=headers,
        data=json.dumps(payload),
        timeout=60,
    )

    if response.status_code >= 400:
        raise RuntimeError(
            f"Failed to write FAILURE pipeline metrics: "
            f"{response.status_code} - {response.text}"
        )


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    require_env()

    log("Writing FAILED pipeline runtime metrics...")

    runtime_seconds = safe_float(
        os.getenv("PIPELINE_RUNTIME_SECONDS"),
        default=0.0,
    )

    error_message = read_recent_logs()

    payload = {
        "run_date_sgt": RUN_DATE_SGT,
        "status": "FAILED",

        "runtime_seconds": runtime_seconds,

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

        "error_message": error_message,
    }

    log(f"Runtime seconds: {runtime_seconds}")
    log(f"Captured error chars: {len(error_message)}")

    post_to_supabase(payload)

    log("[DONE] FAILED pipeline metrics written successfully.")


if __name__ == "__main__":
    main()
