
"""
AI Signal Scoring v7 Alpha Model
================================

Purpose
-------
Build a true cross-sectional alpha model for a 45-stock institutional AI universe.

This script:
1. Reads active AI stock universe from Supabase
2. Reads latest market / valuation / signal / hype data where available
3. Builds subsector-relative alpha factors:
   - relative_momentum_score
   - relative_quality_score
   - relative_efficiency_score
   - relative_valuation_score
   - relative_hype_revision_score
4. Computes alpha_score_v7
5. Ranks stocks within subsector and globally
6. Writes results to public.ai_stock_signal_scores_v7

Required environment variables
------------------------------
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY

Optional
--------
RUN_DATE_SGT=YYYY-MM-DD

Recommended run
---------------
python ai_signal_scoring_v7_alpha_model.py
"""

import os
import math
import json
import time
import datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
from typing import Dict, List, Optional, Any

import requests
import pandas as pd
import numpy as np
# python-dotenv is useful locally, but GitHub Actions injects secrets as environment variables.
# Keep this optional so the script still runs even if python-dotenv is not installed.
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


# =============================================================================
# Configuration
# =============================================================================

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

SGT = ZoneInfo("Asia/Singapore")
RUN_DATE_SGT = os.getenv("RUN_DATE_SGT")
if not RUN_DATE_SGT:
    RUN_DATE_SGT = dt.datetime.now(SGT).date().isoformat()

BASE_DIR = Path(__file__).resolve().parents[1] if Path(__file__).resolve().parent.name == "scripts" else Path.cwd()
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", BASE_DIR / "outputs"))
LOG_DIR = Path(os.getenv("LOG_DIR", BASE_DIR / "logs"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

SOURCE = "GITHUB_ACTIONS_ALPHA_V7_EFFICIENCY_ENABLED"

TABLE_UNIVERSE = "ai_stock_universe"
TABLE_RETURNS = "ai_stock_returns"
TABLE_V6 = "ai_stock_signal_scores_v6"
TABLE_HYPE = "ai_hype_scores"
TABLE_TARGET = "ai_stock_signal_scores_v7"

# If your exact market/valuation source table names differ, the script still runs.
# It will use whichever columns it can find from available tables.
OPTIONAL_TABLES = [
    "ai_stock_fmp_quant_metrics",
    "ai_stock_scores",
    "ai_stock_observations",
    "ai_valuation_inputs",
    "ai_stock_signal_scores",
]


# =============================================================================
# Logging Helpers
# =============================================================================

def log(message: str, level: str = "INFO") -> None:
    now = dt.datetime.now(SGT).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now} SGT] [{level}] {message}", flush=True)


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

        if r.status_code == 404:
            log(f"Table not found or unavailable: {table}", "WARN")
            return pd.DataFrame()

        if r.status_code >= 400:
            log(f"Could not read {table}: {r.status_code} {r.text[:300]}", "WARN")
            return pd.DataFrame()

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
        log("No rows to upsert.", "WARN")
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
            raise RuntimeError(
                f"Upsert failed for {table}: {r.status_code}\n{r.text}"
            )

        log(f"Upserted rows {i + 1} to {i + len(batch)} / {len(rows)}", "OK")


# =============================================================================
# Utility Functions
# =============================================================================

def clean_ticker(s: Any) -> Optional[str]:
    if pd.isna(s):
        return None
    return str(s).strip().upper()


def to_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def safe_col(df: pd.DataFrame, col: str, default=np.nan) -> pd.Series:
    if col in df.columns:
        return to_num(df[col])
    return pd.Series([default] * len(df), index=df.index)


def latest_by_date(df: pd.DataFrame, date_cols: List[str], group_col: str = "ticker") -> pd.DataFrame:
    if df.empty or group_col not in df.columns:
        return df

    df = df.copy()
    for c in date_cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")

    existing = [c for c in date_cols if c in df.columns]
    if not existing:
        return df.drop_duplicates(subset=[group_col], keep="last")

    sort_col = existing[0]
    df = df.sort_values([group_col, sort_col])
    return df.groupby(group_col, as_index=False).tail(1)


def winsorize_series(s: pd.Series, lower: float = 0.10, upper: float = 0.90) -> pd.Series:
    s = to_num(s)
    if s.notna().sum() < 5:
        return s
    lo = s.quantile(lower)
    hi = s.quantile(upper)
    return s.clip(lo, hi)


def percentile_0_100(s: pd.Series, higher_is_better: bool = True) -> pd.Series:
    s = to_num(s)
    if s.notna().sum() == 0:
        return pd.Series([50.0] * len(s), index=s.index)

    if s.notna().sum() == 1:
        return s.apply(lambda x: 50.0 if pd.notna(x) else 50.0)

    ranked = s.rank(pct=True, method="average") * 100.0
    if not higher_is_better:
        ranked = 100.0 - ranked + (100.0 / s.notna().sum())

    return ranked.fillna(50.0).clip(0, 100)


def subsector_percentile(
    df: pd.DataFrame,
    value_col: str,
    higher_is_better: bool = True,
    subsector_col: str = "ai_subsector",
) -> pd.Series:
    if value_col not in df.columns:
        return pd.Series([50.0] * len(df), index=df.index)

    result = pd.Series(index=df.index, dtype=float)

    for _, idx in df.groupby(subsector_col).groups.items():
        group_s = winsorize_series(df.loc[idx, value_col])
        result.loc[idx] = percentile_0_100(group_s, higher_is_better=higher_is_better)

    return result.fillna(50.0).clip(0, 100)


def weighted_average(df: pd.DataFrame, components: Dict[str, float]) -> pd.Series:
    total = pd.Series([0.0] * len(df), index=df.index)
    weight_sum = pd.Series([0.0] * len(df), index=df.index)

    for col, weight in components.items():
        if col not in df.columns:
            continue

        vals = to_num(df[col])
        mask = vals.notna()
        total.loc[mask] += vals.loc[mask] * weight
        weight_sum.loc[mask] += weight

    out = total / weight_sum.replace(0, np.nan)
    return out.fillna(50.0).clip(0, 100)


def label_from_alpha(score: float) -> str:
    if pd.isna(score):
        return "NEUTRAL"
    if score >= 80:
        return "STRONG_ALPHA"
    if score >= 65:
        return "ALPHA"
    if score >= 45:
        return "NEUTRAL"
    return "AVOID"


# =============================================================================
# Data Loading
# =============================================================================

def load_universe() -> pd.DataFrame:
    df = sb_get(
        TABLE_UNIVERSE,
        {
            "select": "ticker,company_name,ai_subsector,asset_class,theme,is_active",
            "is_active": "eq.true",
        },
    )

    if df.empty:
        raise RuntimeError("No active stocks found in ai_stock_universe.")

    df["ticker"] = df["ticker"].apply(clean_ticker)
    df = df.dropna(subset=["ticker", "ai_subsector"]).drop_duplicates("ticker")

    log(f"Loaded active universe: {len(df)} stocks", "OK")
    return df


def load_latest_returns() -> pd.DataFrame:
    df = sb_get(TABLE_RETURNS, {"select": "*"})

    if df.empty:
        log("ai_stock_returns unavailable or empty.", "WARN")
        return pd.DataFrame()

    df["ticker"] = df["ticker"].apply(clean_ticker)

    date_candidates = ["run_date_sgt", "date", "price_date", "as_of_date"]
    df = latest_by_date(df, date_candidates)

    log(f"Loaded latest returns rows: {len(df)}", "OK")
    return df


def load_latest_v6() -> pd.DataFrame:
    df = sb_get(TABLE_V6, {"select": "*"})

    if df.empty:
        log("ai_stock_signal_scores_v6 unavailable or empty.", "WARN")
        return pd.DataFrame()

    df["ticker"] = df["ticker"].apply(clean_ticker)
    df = latest_by_date(df, ["run_date_sgt", "created_at"])

    log(f"Loaded latest v6 signal rows: {len(df)}", "OK")
    return df


def load_latest_hype() -> pd.DataFrame:
    df = sb_get(TABLE_HYPE, {"select": "*"})

    if df.empty:
        log("ai_hype_scores unavailable or empty.", "WARN")
        return pd.DataFrame()

    df["ticker"] = df["ticker"].apply(clean_ticker)
    df = latest_by_date(df, ["run_date", "run_date_sgt", "created_at"])

    log(f"Loaded latest hype rows: {len(df)}", "OK")
    return df


def load_optional_tables() -> Dict[str, pd.DataFrame]:
    out = {}
    for table in OPTIONAL_TABLES:
        df = sb_get(table, {"select": "*"})
        if not df.empty and "ticker" in df.columns:
            df["ticker"] = df["ticker"].apply(clean_ticker)
            df = latest_by_date(df, ["run_date_sgt", "run_date", "created_at", "date"])
            log(f"Loaded optional table {table}: {len(df)} rows", "OK")
            out[table] = df
        else:
            log(f"Optional table skipped: {table}", "INFO")
    return out


# =============================================================================
# Feature Engineering
# =============================================================================

def merge_features(universe: pd.DataFrame, returns: pd.DataFrame, v6: pd.DataFrame, hype: pd.DataFrame, optional: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    df = universe.copy()

    def merge_prefixed(base: pd.DataFrame, right: pd.DataFrame, prefix: str) -> pd.DataFrame:
        if right.empty or "ticker" not in right.columns:
            return base

        right = right.copy()
        cols = [c for c in right.columns if c != "ticker"]
        right = right[["ticker"] + cols]
        rename = {c: f"{prefix}_{c}" for c in cols if c not in ["ticker"]}
        right = right.rename(columns=rename)

        return base.merge(right, on="ticker", how="left")

    df = merge_prefixed(df, returns, "ret")
    df = merge_prefixed(df, v6, "v6")
    df = merge_prefixed(df, hype, "hype")

    for name, odf in optional.items():
        df = merge_prefixed(df, odf, name)

    return df


def first_available_numeric(df: pd.DataFrame, candidates: List[str], default=np.nan) -> pd.Series:
    out = pd.Series([default] * len(df), index=df.index, dtype=float)

    for col in candidates:
        if col in df.columns:
            vals = to_num(df[col])
            out = out.where(out.notna(), vals)

    return out


def build_base_metrics(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Momentum inputs
    df["m_return_20d"] = first_available_numeric(df, [
        "ret_return_20d", "ret_ret_20d", "ret_forward_return_20d",
        "ai_stock_observations_return_20d", "ai_stock_scores_momentum_change_20d",
        "v6_momentum_score"
    ])

    df["m_return_60d"] = first_available_numeric(df, [
        "ret_return_60d", "ret_ret_60d", "ret_forward_return_60d",
        "ai_stock_observations_return_60d", "v6_momentum_score"
    ])

    df["m_price_vs_200dma"] = first_available_numeric(df, [
        "ret_price_vs_200dma_pct",
        "ai_stock_observations_price_vs_200dma_pct",
        "ai_stock_scores_price_vs_200dma_pct",
        "v6_momentum_score"
    ])

    # Valuation inputs
    df["v_pe"] = first_available_numeric(df, [
        "ai_valuation_inputs_pe", "ai_valuation_inputs_pe_ratio", "ai_valuation_inputs_trailing_pe",
        "ai_stock_scores_pe", "ai_stock_signal_scores_pe", "v6_valuation_score"
    ])

    df["v_ev_ebitda"] = first_available_numeric(df, [
        "ai_valuation_inputs_ev_ebitda", "ai_valuation_inputs_enterprise_value_over_ebitda",
        "ai_stock_scores_ev_ebitda", "ai_stock_signal_scores_ev_ebitda", "v6_valuation_score"
    ])

    df["v_fcf_yield"] = first_available_numeric(df, [
        "ai_valuation_inputs_fcf_yield", "ai_valuation_inputs_free_cash_flow_yield",
        "ai_stock_scores_fcf_yield", "ai_stock_signal_scores_fcf_yield", "v6_valuation_score"
    ])

    # Quality inputs
    df["q_gross_margin"] = first_available_numeric(df, [
        "ai_valuation_inputs_gross_margin", "ai_stock_scores_gross_margin",
        "ai_stock_signal_scores_gross_margin", "v6_quality_score"
    ])

    df["q_ebitda_margin"] = first_available_numeric(df, [
        "ai_valuation_inputs_ebitda_margin", "ai_stock_scores_ebitda_margin",
        "ai_stock_signal_scores_ebitda_margin", "v6_quality_score"
    ])

    df["q_revenue_growth"] = first_available_numeric(df, [
        "ai_valuation_inputs_revenue_growth", "ai_stock_scores_revenue_growth",
        "ai_stock_signal_scores_revenue_growth", "v6_growth_score"
    ])

    # Efficiency inputs
    df["e_revenue_per_ev"] = first_available_numeric(df, [
        "ai_stock_fmp_quant_metrics_revenue_per_ev",
        "ai_valuation_inputs_revenue_per_ev",
        "ai_stock_scores_revenue_per_ev",
        "ai_stock_signal_scores_revenue_per_ev"
    ])

    df["e_ebitda_per_ev"] = first_available_numeric(df, [
        "ai_stock_fmp_quant_metrics_ebitda_per_ev",
        "ai_valuation_inputs_ebitda_per_ev",
        "ai_stock_scores_ebitda_per_ev",
        "ai_stock_signal_scores_ebitda_per_ev"
    ])

    df["e_fcf_per_ev"] = first_available_numeric(df, [
        "ai_stock_fmp_quant_metrics_fcf_per_ev",
        "ai_valuation_inputs_fcf_per_ev",
        "ai_stock_scores_fcf_per_ev",
        "ai_stock_signal_scores_fcf_per_ev"
    ])

    # Hype / sentiment inputs
    df["h_hype_score"] = first_available_numeric(df, [
        "hype_hype_score", "ai_stock_scores_ai_hype_score", "v6_ai_hype_score"
    ])

    df["h_sentiment"] = first_available_numeric(df, [
        "hype_avg_sentiment_score", "hype_sentiment_z", "ai_stock_scores_sentiment_score"
    ])

    df["h_news_volume"] = first_available_numeric(df, [
        "hype_news_volume_z", "hype_article_count", "ai_stock_scores_news_volume_z"
    ])

    df["h_hype_change"] = first_available_numeric(df, [
        "hype_hype_change", "hype_hype_score_change", "ai_stock_scores_hype_change"
    ])

    # Risk inputs
    df["risk_overheating"] = first_available_numeric(df, [
        "v6_risk_overheating_score", "v6_overheating_score", "v6_risk_penalty",
        "ai_stock_scores_overheating_score", "ai_stock_scores_overall_ai_risk_score"
    ])

    return df


def build_relative_factors(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Component percentiles by subsector
    df["p_return_20d_rel"] = subsector_percentile(df, "m_return_20d", True)
    df["p_return_60d_rel"] = subsector_percentile(df, "m_return_60d", True)
    df["p_price_vs_200dma_rel"] = subsector_percentile(df, "m_price_vs_200dma", True)

    df["p_pe_rel"] = subsector_percentile(df, "v_pe", False)
    df["p_ev_ebitda_rel"] = subsector_percentile(df, "v_ev_ebitda", False)
    df["p_fcf_yield_rel"] = subsector_percentile(df, "v_fcf_yield", True)

    df["p_gross_margin_rel"] = subsector_percentile(df, "q_gross_margin", True)
    df["p_ebitda_margin_rel"] = subsector_percentile(df, "q_ebitda_margin", True)
    df["p_revenue_growth_rel"] = subsector_percentile(df, "q_revenue_growth", True)

    df["p_revenue_per_ev_rel"] = subsector_percentile(df, "e_revenue_per_ev", True)
    df["p_ebitda_per_ev_rel"] = subsector_percentile(df, "e_ebitda_per_ev", True)
    df["p_fcf_per_ev_rel"] = subsector_percentile(df, "e_fcf_per_ev", True)

    df["p_sentiment_rel"] = subsector_percentile(df, "h_sentiment", True)
    df["p_news_volume_rel"] = subsector_percentile(df, "h_news_volume", True)
    df["p_hype_change_rel"] = subsector_percentile(df, "h_hype_change", True)

    # Factor scores
    df["relative_momentum_score"] = weighted_average(df, {
        "p_return_20d_rel": 0.40,
        "p_return_60d_rel": 0.35,
        "p_price_vs_200dma_rel": 0.25,
    })

    df["relative_quality_score"] = weighted_average(df, {
        "p_gross_margin_rel": 0.35,
        "p_ebitda_margin_rel": 0.30,
        "p_revenue_growth_rel": 0.20,
        "p_fcf_yield_rel": 0.15,
    })

    df["relative_efficiency_score"] = weighted_average(df, {
        "p_revenue_per_ev_rel": 0.40,
        "p_ebitda_per_ev_rel": 0.45,
        "p_fcf_per_ev_rel": 0.15,
    })

    df["relative_valuation_score"] = weighted_average(df, {
        "p_pe_rel": 0.35,
        "p_ev_ebitda_rel": 0.35,
        "p_fcf_yield_rel": 0.30,
    })

    df["relative_hype_revision_score"] = weighted_average(df, {
        "p_sentiment_rel": 0.50,
        "p_news_volume_rel": 0.30,
        "p_hype_change_rel": 0.20,
    })

    return df


def build_alpha_score(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    raw_alpha = (
        df["relative_momentum_score"] * 0.30
        + df["relative_quality_score"] * 0.25
        + df["relative_efficiency_score"] * 0.20
        + df["relative_valuation_score"] * 0.15
        + df["relative_hype_revision_score"] * 0.10
    )

    # Risk penalty is deliberately light.
    # v7 is an alpha model, not a pure overheating/risk ranking model.
    overheating = to_num(df["risk_overheating"]).fillna(50).clip(0, 100)
    risk_penalty = np.where(overheating > 80, (overheating - 80) * 0.15, 0)

    # Hype exhaustion penalty:
    # High hype + weakening momentum is dangerous.
    hype = to_num(df["h_hype_score"]).fillna(50)
    momentum = to_num(df["relative_momentum_score"]).fillna(50)
    hype_exhaustion = np.where((hype > 85) & (momentum < 50), 5.0, 0.0)

    df["risk_penalty"] = (risk_penalty + hype_exhaustion).clip(0, 10)

    df["alpha_score_v7"] = (raw_alpha - df["risk_penalty"]).clip(0, 100)

    df["subsector_rank"] = (
        df.groupby("ai_subsector")["alpha_score_v7"]
        .rank(method="first", ascending=False)
        .astype(int)
    )

    df["global_rank"] = (
        df["alpha_score_v7"]
        .rank(method="first", ascending=False)
        .astype(int)
    )

    df["signal_label"] = df["alpha_score_v7"].apply(label_from_alpha)

    df["portfolio_candidate"] = (
        (df["subsector_rank"] <= 2)
        & (df["alpha_score_v7"] >= 60)
    )

    return df


def prepare_output_rows(df: pd.DataFrame) -> List[Dict[str, Any]]:
    out_cols = [
        "run_date_sgt",
        "ticker",
        "company_name",
        "ai_subsector",
        "relative_momentum_score",
        "relative_quality_score",
        "relative_efficiency_score",
        "relative_valuation_score",
        "relative_hype_revision_score",
        "risk_penalty",
        "alpha_score_v7",
        "subsector_rank",
        "global_rank",
        "signal_label",
        "portfolio_candidate",
        "source",
    ]

    out = df.copy()
    out["run_date_sgt"] = RUN_DATE_SGT
    out["source"] = SOURCE

    for col in [
        "relative_momentum_score",
        "relative_quality_score",
        "relative_efficiency_score",
        "relative_valuation_score",
        "relative_hype_revision_score",
        "risk_penalty",
        "alpha_score_v7",
    ]:
        out[col] = to_num(out[col]).round(4)

    out = out[out_cols]

    rows = []
    for _, r in out.iterrows():
        item = {}
        for c in out_cols:
            val = r[c]
            if pd.isna(val):
                item[c] = None
            elif isinstance(val, (np.integer,)):
                item[c] = int(val)
            elif isinstance(val, (np.floating,)):
                item[c] = float(val)
            else:
                item[c] = val
        rows.append(item)

    return rows


def print_diagnostics(df: pd.DataFrame) -> None:
    print("\n" + "=" * 100)
    print("AI Signal Scoring v7 Alpha Model Diagnostics - Efficiency Enabled")
    print("=" * 100)

    print(f"Run date: {RUN_DATE_SGT}")
    print(f"Stocks scored: {len(df)}")
    print(f"Subsectors: {df['ai_subsector'].nunique()}")

    print("\nEfficiency field coverage:")
    for col in ["e_revenue_per_ev", "e_ebitda_per_ev", "e_fcf_per_ev", "relative_efficiency_score"]:
        if col in df.columns:
            valid = pd.to_numeric(df[col], errors="coerce").notna().sum()
            print(f"{col}: {valid}/{len(df)} valid")
        else:
            print(f"{col}: 0/{len(df)} valid")

    print("\nTop 15 global alpha candidates:")
    cols = [
        "ticker", "company_name", "ai_subsector",
        "alpha_score_v7", "subsector_rank", "global_rank",
        "relative_momentum_score", "relative_quality_score",
        "relative_efficiency_score", "relative_valuation_score",
        "signal_label", "portfolio_candidate"
    ]
    view_cols = [c for c in cols if c in df.columns]
    print(
        df.sort_values("alpha_score_v7", ascending=False)[view_cols]
        .head(15)
        .to_string(index=False)
    )

    print("\nSubsector candidate counts:")
    print(
        df.groupby("ai_subsector")
        .agg(
            stocks=("ticker", "count"),
            candidates=("portfolio_candidate", "sum"),
            avg_alpha=("alpha_score_v7", "mean"),
            max_alpha=("alpha_score_v7", "max"),
        )
        .sort_values("max_alpha", ascending=False)
        .round(2)
        .to_string()
    )

    print("\nSignal label distribution:")
    print(df["signal_label"].value_counts(dropna=False).to_string())

    print("=" * 100 + "\n")


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    require_env()
    log(f"Starting v7 alpha scoring pipeline. RUN_DATE_SGT={RUN_DATE_SGT}")
    log(f"Output directory: {OUTPUT_DIR}")

    universe = load_universe()
    returns = load_latest_returns()
    v6 = load_latest_v6()
    hype = load_latest_hype()
    optional = load_optional_tables()

    df = merge_features(universe, returns, v6, hype, optional)
    df = build_base_metrics(df)
    df = build_relative_factors(df)
    df = build_alpha_score(df)

    print_diagnostics(df)

    rows = prepare_output_rows(df)

    output_csv = OUTPUT_DIR / f"ai_stock_signal_scores_v7_{RUN_DATE_SGT}.csv"
    output_json = OUTPUT_DIR / f"ai_stock_signal_scores_v7_{RUN_DATE_SGT}.json"
    pd.DataFrame(rows).to_csv(output_csv, index=False)
    pd.DataFrame(rows).to_json(output_json, orient="records", indent=2)
    log(f"Saved monitoring artifact CSV: {output_csv}", "OK")
    log(f"Saved monitoring artifact JSON: {output_json}", "OK")

    sb_upsert(TABLE_TARGET, rows, "run_date_sgt,ticker")

    if len(rows) == 0:
        raise RuntimeError("No rows were generated for ai_stock_signal_scores_v7.")

    log(f"v7 alpha scoring complete. Rows written to {TABLE_TARGET}: {len(rows)}", "DONE")


if __name__ == "__main__":
    main()
