import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import requests

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

RUN_DATE_SGT = datetime.now(
    ZoneInfo("Asia/Singapore")
).date().isoformat()

SUMMARY_FILE = "outputs/ai_portfolio_v7_summary_latest.csv"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates",
}

if not os.path.exists(SUMMARY_FILE):
    raise RuntimeError(f"Summary file not found: {SUMMARY_FILE}")

df = pd.read_csv(SUMMARY_FILE)

if df.empty:
    raise RuntimeError("Summary file is empty")

row = df.iloc[0]

payload = {
    "run_date_sgt": RUN_DATE_SGT,
    "status": "SUCCESS",

    "signal_rows": int(row.get("signal_rows", 0)),
    "portfolio_rows": int(row.get("portfolio_rows", 0)),
    "subsectors": int(row.get("subsectors", 0)),
    "portfolio_subsectors": int(row.get("portfolio_subsectors", 0)),

    "cash_weight": float(row.get("cash_weight", 0)),
    "avg_alpha_score": float(row.get("avg_alpha_score", 0)),
    "top_alpha_ticker": str(row.get("top_alpha_ticker", "")),

    "github_run_id": os.getenv("GITHUB_RUN_ID"),
    "github_workflow": os.getenv("GITHUB_WORKFLOW"),
    "github_repository": os.getenv("GITHUB_REPOSITORY"),
    "github_branch": os.getenv("GITHUB_REF_NAME"),
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
        f"Failed to write pipeline metrics: "
        f"{response.status_code} - {response.text}"
    )

print("[DONE] Pipeline metrics written successfully.")