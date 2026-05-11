import os
import json
import math
import requests
import pandas as pd

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates",
}


def fetch_table(table_name, select="*", filters=None, limit=None):
    url = f"{SUPABASE_URL}/rest/v1/{table_name}"

    params = {"select": select}

    if limit:
        params["limit"] = limit

    if filters:
        params.update(filters)

    response = requests.get(url, headers=HEADERS, params=params)

    if not response.ok:
        print("FETCH FAILED")
        print("Table:", table_name)
        print("Status:", response.status_code)
        print("Response:", response.text)

    response.raise_for_status()
    return response.json()


def clean_json_value(value):
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None

    return value


def clean_row(row):
    return {key: clean_json_value(value) for key, value in row.items()}


def upsert_rows(table_name, rows, on_conflict):
    if not rows:
        return 0

    clean_rows = [clean_row(row) for row in rows]

    url = f"{SUPABASE_URL}/rest/v1/{table_name}"

    headers = HEADERS.copy()
    headers["Prefer"] = "resolution=merge-duplicates"

    response = requests.post(
        url,
        headers=headers,
        params={"on_conflict": on_conflict},
        data=json.dumps(clean_rows, allow_nan=False),
    )

    if not response.ok:
        print("UPSERT FAILED")
        print("Table:", table_name)
        print("Status:", response.status_code)
        print("Response:", response.text)
        print("Rows attempted:", len(clean_rows))
        print("First row sample:", clean_rows[0] if clean_rows else None)

    response.raise_for_status()
    return len(clean_rows)


def calculate_return(prices_df, ticker, current_date, lookback_days):
    subset = prices_df[prices_df["ticker"] == ticker].sort_values("date")

    if subset.empty:
        return 0

    subset = subset[subset["date"] <= current_date]

    if len(subset) < lookback_days:
        return 0

    latest = subset.iloc[-1]["close"]
    previous = subset.iloc[-lookback_days]["close"]

    if pd.isna(latest) or pd.isna(previous):
        return 0

    if previous == 0:
        return 0

    return float((latest - previous) / previous * 100)


def regime_from_score(score):
    if score is None:
        return "NEUTRAL"

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
