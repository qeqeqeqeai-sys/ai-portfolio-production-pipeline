
"""
AI Portfolio Engine v7 - Alpha Score v7
=======================================

Purpose
-------
Build a subsector-neutral AI equity portfolio using ai_stock_signal_scores_v7.alpha_score_v7.

This portfolio engine:
1. Reads latest v7 alpha scores from Supabase
2. Selects top candidates using subsector-neutral logic
3. Uses alpha_score_v7 instead of older risk/overheating scores
4. Limits concentration by stock and subsector
5. Adds CASH when alpha breadth is weak
6. Writes portfolio output into Supabase

Required .env variables
-----------------------
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY

Optional .env variables
-----------------------
RUN_DATE_SGT=YYYY-MM-DD

Recommended table
-----------------
public.ai_portfolio_engine_v7

Run
---
python ai_portfolio_engine_v7_alpha_score.py
"""

import os
import json
import datetime as dt
from typing import Dict, List, Any, Optional

import requests
import pandas as pd
import numpy as np
from dotenv import load_dotenv


# =============================================================================
# Environment
# =============================================================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

RUN_DATE_SGT = os.getenv("RUN_DATE_SGT")
if not RUN_DATE_SGT:
    RUN_DATE_SGT = dt.datetime.utcnow().date().isoformat()

SOURCE = "PYTHON_PORTFOLIO_ENGINE_V7_ALPHA_SCORE"

TABLE_SIGNAL_V7 = "ai_stock_signal_scores_v7"
TABLE_TARGET = "ai_portfolio_engine_v7"


# =============================================================================
# Portfolio Configuration
# =============================================================================

MAX_HOLDINGS = 15
MIN_HOLDINGS = 8

MAX_PER_SUBSECTOR = 2
MIN_SUBSECTORS = 6

MIN_ALPHA_SCORE = 60.0
STRONG_ALPHA_SCORE = 65.0

MAX_STOCK_WEIGHT = 0.10
MAX_SUBSECTOR_WEIGHT = 0.25

BASE_CASH_WEIGHT_IF_WEAK = 0.20

# Weighting blend:
# - base equal weight gives stability
# - alpha tilt rewards stronger signals
ALPHA_TILT_STRENGTH = 0.35

# If too few valid alpha candidates exist, portfolio holds cash.
MIN_VALID_CANDIDATES_FOR_FULLY_INVESTED = 8


# =============================================================================
# Supabase Helpers
# =============================================================================

def require_env() -> None:
    missing = []
    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")
    if not SUPABASE_KEY:
        missing.append("SUPABASE_SERVICE_ROLE_KEY")
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")


def supabase_headers(prefer: Optional[str] = None) -> Dict[str, str]:
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


def sb_get(table: str, params: Dict[str, str], limit: int = 10000) -> pd.DataFrame:
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    all_rows = []
    offset = 0

    while True:
        p = dict(params)
        p["limit"] = str(limit)
        p["offset"] = str(offset)

        r = requests.get(url, headers=supabase_headers(), params=p, timeout=60)

        if r.status_code >= 400:
            raise RuntimeError(f"Could not read {table}: {r.status_code}\n{r.text}")

        rows = r.json()

        if not rows:
            break

        all_rows.extend(rows)

        if len(rows) < limit:
            break

        offset += limit

    return pd.DataFrame(all_rows)


def sb_upsert(table: str, rows: List[Dict[str, Any]], conflict_cols: str, batch_size: int = 500) -> None:
    if not rows:
        print("[WARN] No rows to upsert.")
        return

    url = f"{SUPABASE_URL}/rest/v1/{table}"
    params = {"on_conflict": conflict_cols}

    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]

        r = requests.post(
            url,
            headers=supabase_headers("resolution=merge-duplicates"),
            params=params,
            data=json.dumps(batch, default=str),
            timeout=60,
        )

        if r.status_code >= 400:
            raise RuntimeError(f"Upsert failed for {table}: {r.status_code}\n{r.text}")

        print(f"[OK] Upserted rows {i + 1} to {i + len(batch)} / {len(rows)}")


# =============================================================================
# Data Loading
# =============================================================================

def load_latest_v7_scores() -> pd.DataFrame:
    # First try exact run date.
    df = sb_get(
        TABLE_SIGNAL_V7,
        {
            "select": "*",
            "run_date_sgt": f"eq.{RUN_DATE_SGT}",
            "order": "alpha_score_v7.desc",
        },
    )

    # If no rows for current date, use latest available date.
    if df.empty:
        print(f"[WARN] No v7 scores found for RUN_DATE_SGT={RUN_DATE_SGT}. Searching latest available date.")

        latest = sb_get(
            TABLE_SIGNAL_V7,
            {
                "select": "run_date_sgt",
                "order": "run_date_sgt.desc",
                "limit": "1",
            },
        )

        if latest.empty:
            raise RuntimeError("No rows found in ai_stock_signal_scores_v7.")

        latest_date = str(latest.iloc[0]["run_date_sgt"])
        print(f"[INFO] Using latest available v7 score date: {latest_date}")

        df = sb_get(
            TABLE_SIGNAL_V7,
            {
                "select": "*",
                "run_date_sgt": f"eq.{latest_date}",
                "order": "alpha_score_v7.desc",
            },
        )

    if df.empty:
        raise RuntimeError("No v7 alpha scores available.")

    df["ticker"] = df["ticker"].astype(str).str.upper().str.strip()
    df["alpha_score_v7"] = pd.to_numeric(df["alpha_score_v7"], errors="coerce")
    df["subsector_rank"] = pd.to_numeric(df["subsector_rank"], errors="coerce")
    df["global_rank"] = pd.to_numeric(df["global_rank"], errors="coerce")

    df = df.dropna(subset=["ticker", "ai_subsector", "alpha_score_v7"])

    print(f"[OK] Loaded v7 alpha scores: {len(df)} rows")
    print(f"[OK] Score date used: {df['run_date_sgt'].iloc[0]}")

    return df


# =============================================================================
# Portfolio Construction
# =============================================================================

def select_subsector_neutral_candidates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Selects top stocks per subsector using alpha_score_v7.

    Logic:
    - Prefer portfolio_candidate = true if available
    - Require alpha_score_v7 >= MIN_ALPHA_SCORE
    - Max 2 per subsector
    - Max 15 total holdings
    - If fewer than MIN_HOLDINGS, allow best names below threshold as fillers
    """
    df = df.copy()

    if "portfolio_candidate" in df.columns:
        # Supabase may return booleans as bool or strings.
        df["portfolio_candidate_bool"] = df["portfolio_candidate"].astype(str).str.lower().isin(["true", "1", "yes"])
    else:
        df["portfolio_candidate_bool"] = False

    primary = df[
        (
            (df["portfolio_candidate_bool"])
            | (df["subsector_rank"] <= MAX_PER_SUBSECTOR)
        )
        & (df["alpha_score_v7"] >= MIN_ALPHA_SCORE)
    ].copy()

    primary = primary.sort_values(
        ["ai_subsector", "subsector_rank", "alpha_score_v7"],
        ascending=[True, True, False],
    )

    selected = []

    for subsector, g in primary.groupby("ai_subsector"):
        take = g.sort_values("alpha_score_v7", ascending=False).head(MAX_PER_SUBSECTOR)
        selected.append(take)

    if selected:
        portfolio = pd.concat(selected, ignore_index=True)
    else:
        portfolio = pd.DataFrame(columns=df.columns)

    portfolio = portfolio.sort_values("alpha_score_v7", ascending=False).head(MAX_HOLDINGS)

    # If portfolio is too thin, fill with best remaining names while respecting subsector cap.
    if len(portfolio) < MIN_HOLDINGS:
        selected_tickers = set(portfolio["ticker"].tolist())
        subsector_counts = portfolio["ai_subsector"].value_counts().to_dict()

        remaining = df[~df["ticker"].isin(selected_tickers)].sort_values("alpha_score_v7", ascending=False)

        fillers = []
        for _, row in remaining.iterrows():
            if len(portfolio) + len(fillers) >= MIN_HOLDINGS:
                break

            subsector = row["ai_subsector"]
            current_count = subsector_counts.get(subsector, 0)

            if current_count >= MAX_PER_SUBSECTOR:
                continue

            fillers.append(row)
            subsector_counts[subsector] = current_count + 1

        if fillers:
            filler_df = pd.DataFrame(fillers)
            portfolio = pd.concat([portfolio, filler_df], ignore_index=True)

    portfolio = portfolio.drop_duplicates("ticker").sort_values("alpha_score_v7", ascending=False)

    # Hard cap total holdings.
    portfolio = portfolio.head(MAX_HOLDINGS).copy()

    return portfolio


def compute_weights(portfolio: pd.DataFrame) -> pd.DataFrame:
    """
    Builds stable institutional-style weights.

    Weighting method:
    - Equal weight base
    - Alpha tilt using relative score strength
    - Stock cap
    - Subsector cap
    - Cash if alpha breadth weak
    """
    if portfolio.empty:
        return portfolio

    p = portfolio.copy()

    n = len(p)

    # Determine cash allocation.
    if n < MIN_VALID_CANDIDATES_FOR_FULLY_INVESTED:
        cash_weight = BASE_CASH_WEIGHT_IF_WEAK
    else:
        cash_weight = 0.0

    investable_weight = 1.0 - cash_weight

    base_weight = 1.0 / n

    score = pd.to_numeric(p["alpha_score_v7"], errors="coerce").fillna(MIN_ALPHA_SCORE)
    score_min = score.min()
    score_max = score.max()

    if score_max > score_min:
        alpha_strength = (score - score_min) / (score_max - score_min)
    else:
        alpha_strength = pd.Series([0.5] * n, index=p.index)

    # Convert to alpha tilt multiplier.
    # Example: best stock receives modest overweight, not extreme overweight.
    tilt = 1.0 + ALPHA_TILT_STRENGTH * (alpha_strength - alpha_strength.mean())

    raw_weight = base_weight * tilt
    raw_weight = raw_weight / raw_weight.sum() * investable_weight

    p["raw_weight"] = raw_weight

    # Apply single-stock cap.
    p["weight"] = p["raw_weight"].clip(upper=MAX_STOCK_WEIGHT)

    # Redistribute after stock cap.
    capped_total = p["weight"].sum()
    if capped_total > 0:
        p["weight"] = p["weight"] / capped_total * investable_weight

    # Apply subsector cap iteratively.
    for _ in range(5):
        subsector_weights = p.groupby("ai_subsector")["weight"].sum()
        over = subsector_weights[subsector_weights > MAX_SUBSECTOR_WEIGHT]

        if over.empty:
            break

        for subsector, total_weight in over.items():
            idx = p["ai_subsector"] == subsector
            scale = MAX_SUBSECTOR_WEIGHT / total_weight
            p.loc[idx, "weight"] = p.loc[idx, "weight"] * scale

        current_total = p["weight"].sum()
        if current_total <= 0:
            break

        under_idx = p.groupby("ai_subsector")["weight"].transform("sum") < MAX_SUBSECTOR_WEIGHT
        room = investable_weight - current_total

        if room <= 0.000001 or not under_idx.any():
            break

        p.loc[under_idx, "weight"] += room * (p.loc[under_idx, "weight"] / p.loc[under_idx, "weight"].sum())

        p["weight"] = p["weight"].clip(upper=MAX_STOCK_WEIGHT)

    # Final normalize to investable weight if possible.
    total = p["weight"].sum()
    if total > 0:
        p["weight"] = p["weight"] / total * investable_weight

    p["cash_weight"] = cash_weight

    return p


def add_actions(portfolio: pd.DataFrame) -> pd.DataFrame:
    """
    Placeholder action logic.

    For now:
    - All selected stocks are TARGET_HOLDING
    - Cash is CASH_RESERVE

    In a later version, we can compare against previous portfolio and generate:
    BUY_NEW / HOLD / REBALANCE / SELL / CASH_HOLD
    """
    p = portfolio.copy()
    p["action"] = "TARGET_HOLDING"
    return p


def build_output_rows(portfolio: pd.DataFrame) -> List[Dict[str, Any]]:
    rows = []

    if portfolio.empty:
        rows.append({
            "run_date_sgt": RUN_DATE_SGT,
            "ticker": "CASH",
            "company_name": "Cash",
            "ai_subsector": "Cash",
            "alpha_score_v7": None,
            "subsector_rank": None,
            "global_rank": None,
            "signal_label": "CASH",
            "portfolio_weight": 1.0,
            "raw_weight": 1.0,
            "cash_weight": 1.0,
            "action": "CASH_RESERVE",
            "source": SOURCE,
        })
        return rows

    p = portfolio.copy()

    for _, r in p.iterrows():
        rows.append({
            "run_date_sgt": RUN_DATE_SGT,
            "ticker": r.get("ticker"),
            "company_name": r.get("company_name"),
            "ai_subsector": r.get("ai_subsector"),
            "alpha_score_v7": round(float(r.get("alpha_score_v7")), 4) if pd.notna(r.get("alpha_score_v7")) else None,
            "subsector_rank": int(r.get("subsector_rank")) if pd.notna(r.get("subsector_rank")) else None,
            "global_rank": int(r.get("global_rank")) if pd.notna(r.get("global_rank")) else None,
            "signal_label": r.get("signal_label"),
            "portfolio_weight": round(float(r.get("weight", 0)), 6),
            "raw_weight": round(float(r.get("raw_weight", r.get("weight", 0))), 6),
            "cash_weight": round(float(r.get("cash_weight", 0)), 6),
            "action": r.get("action", "TARGET_HOLDING"),
            "source": SOURCE,
        })

    cash_weight = float(p["cash_weight"].iloc[0]) if "cash_weight" in p.columns and len(p) else 0.0

    if cash_weight > 0.000001:
        rows.append({
            "run_date_sgt": RUN_DATE_SGT,
            "ticker": "CASH",
            "company_name": "Cash",
            "ai_subsector": "Cash",
            "alpha_score_v7": None,
            "subsector_rank": None,
            "global_rank": None,
            "signal_label": "CASH",
            "portfolio_weight": round(cash_weight, 6),
            "raw_weight": round(cash_weight, 6),
            "cash_weight": round(cash_weight, 6),
            "action": "CASH_RESERVE",
            "source": SOURCE,
        })

    return rows


def print_diagnostics(df: pd.DataFrame, portfolio: pd.DataFrame, rows: List[Dict[str, Any]]) -> None:
    print("\n" + "=" * 100)
    print("AI Portfolio Engine v7 - alpha_score_v7")
    print("=" * 100)

    print(f"Run date: {RUN_DATE_SGT}")
    print(f"Input v7 score rows: {len(df)}")
    print(f"Selected equity holdings: {len(portfolio)}")

    if not portfolio.empty:
        print(f"Subsectors represented: {portfolio['ai_subsector'].nunique()}")
        print(f"Average alpha_score_v7: {portfolio['alpha_score_v7'].mean():.2f}")
        print(f"Minimum alpha_score_v7: {portfolio['alpha_score_v7'].min():.2f}")
        print(f"Maximum alpha_score_v7: {portfolio['alpha_score_v7'].max():.2f}")

        view_cols = [
            "ticker",
            "company_name",
            "ai_subsector",
            "alpha_score_v7",
            "subsector_rank",
            "global_rank",
            "weight",
            "signal_label",
            "action",
        ]

        print("\nPortfolio holdings:")
        print(
            portfolio[view_cols]
            .sort_values("weight", ascending=False)
            .to_string(index=False)
        )

        print("\nSubsector weights:")
        print(
            portfolio.groupby("ai_subsector")["weight"]
            .sum()
            .sort_values(ascending=False)
            .round(4)
            .to_string()
        )

    total_weight = sum(float(r["portfolio_weight"]) for r in rows)
    cash_weight = sum(float(r["portfolio_weight"]) for r in rows if r["ticker"] == "CASH")

    print(f"\nTotal portfolio weight: {total_weight:.4f}")
    print(f"Cash weight: {cash_weight:.4f}")

    print("=" * 100 + "\n")


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    require_env()

    df = load_latest_v7_scores()
    selected = select_subsector_neutral_candidates(df)
    weighted = compute_weights(selected)
    weighted = add_actions(weighted)

    rows = build_output_rows(weighted)

    print_diagnostics(df, weighted, rows)

    sb_upsert(TABLE_TARGET, rows, "run_date_sgt,ticker")

    print(f"[DONE] Portfolio engine v7 complete. Rows written to {TABLE_TARGET}: {len(rows)}")


if __name__ == "__main__":
    main()
