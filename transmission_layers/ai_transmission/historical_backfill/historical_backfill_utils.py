import os
import json
import requests
import pandas as pd
from datetime import datetime

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}


def fetch_table(table_name, select="*", filters=None, limit=None):
    url = f"{SUPABASE_URL}/rest/v1/{table_name}"

    params = {
        "select": select
    }

    if limit:
        params["limit"] = limit

    if filters:
        params.update(filters)

    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()

    return response.json()


def upsert_rows(table_name, rows, on_conflict):
    if not rows:
        return 0

    url = f"{SUPABASE_URL}/rest/v1/{table_name}"

    headers = HEADERS.copy()
    headers["Prefer"] = "resolution=merge-duplicates"

    response = requests.post(
        url,
        headers=headers,
        params={
            "on_conflict": on_conflict
        },
        data=json.dumps(rows)
    )

    response.raise_for_status()

    return len(rows)


def calculate_return(prices_df, ticker, current_date, lookback_days):
    subset = prices_df[
        prices_df["ticker"] == ticker
    ].sort_values("date")

    if subset.empty:
        return 0

    subset = subset[subset["date"] <= current_date]

    if len(subset) < lookback_days:
        return 0

    latest = subset.iloc[-1]["close"]
    previous = subset.iloc[-lookback_days]["close"]

    if previous in [0, None]:
        return 0

    return float((latest - previous) / previous * 100)


def regime_from_score(score):
    if score >= 75:
        return "OVERHEATED"
    elif score >= 55:
        return "BULLISH"
    elif score >= 45:
        return "NEUTRAL"
    elif score >= 30:
        return "BEARISH"
    else:
        return "COLLAPSING"
