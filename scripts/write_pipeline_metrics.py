import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

import pandas as pd
import requests


# =============================================================================
# Configuration
# =============================================================================

SGT = ZoneInfo("Asia/Singapore")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

RUN_DATE_SGT = datetime.now(SGT).date().isoformat()

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "outputs"))
SUMMARY_FILE = OUTPUT_DIR / "ai_portfolio_v7_summary_latest.csv"

TABLE_NAME = "production_pipeline_runs"


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


def safe_int(value, default=None):
    try:
        if pd.isna(value):
            return default
        return int(float(value))
    except Exception:
        return default


def safe_float(value, default=None):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def safe_str(value, default=None):
    try:
        if pd.isna(value):
            return default
        return str(value)
    except Exception:
        return default


def read_summary() -> pd.Series:
    if not SUMMARY_FILE.exists():
        raise RuntimeError(f"Summary file not found: {SUMMARY_FILE}")

    df = pd.read_csv(SUMMARY_FILE)

    if df.empty:
        raise RuntimeError(f"Summary file is empty: {SUMMARY_FILE}")

    return df.iloc[0]


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
            f"Failed to write pipeline metrics: "
            f"{response.status_code} - {response.text}"
        )


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    require_env()

    log("Writing SUCCESS pipeline runtime metrics...")

    row = read_summary()

    runtime_seconds = safe_float(
        os.getenv("PIPELINE_RUNTIME_SECONDS"),
        default=0.0,
    )

    payload = {
        "run_date_sgt": RUN_DATE_SGT,
        "status": "SUCCESS",

        "runtime_seconds": runtime_seconds,

        "signal_rows": safe_int(row.get("signal_rows")),
        "portfolio_rows": safe_int(row.get("portfolio_rows")),

        "subsectors": safe_int(row.get("subsectors_in_signal_universe")),
        "portfolio_subsectors": safe_int(row.get("subsectors_in_portfolio")),

        "cash_weight": safe_float(row.get("cash_weight")),
        "avg_alpha_score": safe_float(row.get("avg_alpha_score")),
        "top_alpha_ticker": safe_str(row.get("top_alpha_ticker")),

        "github_run_id": os.getenv("GITHUB_RUN_ID"),
        "github_workflow": os.getenv("GITHUB_WORKFLOW"),
        "github_repository": os.getenv("GITHUB_REPOSITORY"),
        "github_branch": os.getenv("GITHUB_REF_NAME"),

        "error_message": None,
    }

    log(f"Runtime seconds: {runtime_seconds}")
    log(f"Signal rows: {payload['signal_rows']}")
    log(f"Portfolio rows: {payload['portfolio_rows']}")
    log(f"Cash weight: {payload['cash_weight']}")
    log(f"Top alpha ticker: {payload['top_alpha_ticker']}")

    post_to_supabase(payload)

    log("[DONE] SUCCESS pipeline metrics written successfully.")


if __name__ == "__main__":
    main()
