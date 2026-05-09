#!/usr/bin/env python3
"""
AI Portfolio Monitoring v1 - GitHub Actions Ready
=================================================

def log(message, level="INFO"):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    now = datetime.now(ZoneInfo("Asia/Singapore")).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now} SGT] [{level}] {message}", flush=True)


Purpose
-------
Monitor the daily AI portfolio production pipeline after:

1. ai_signal_scoring_v7_alpha_model_efficiency_enabled.py
2. ai_portfolio_engine_v7_alpha_score.py

This script reads from Supabase REST API only and produces GitHub Actions artifacts:

- HTML monitoring report
- CSV production summary
- CSV latest v7 alpha scores
- CSV portfolio holdings
- CSV subsector allocation
- CSV top alpha candidates
- PNG monitoring charts

Required environment variables
------------------------------
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY

Optional environment variables
------------------------------
RUN_DATE_SGT=YYYY-MM-DD
SIGNAL_V7_TABLE=ai_stock_signal_scores_v7
PORTFOLIO_V7_TABLE=ai_portfolio_engine_v7
OUTPUT_DIR=outputs

Recommended GitHub Actions run
------------------------------
python scripts/ai_portfolio_monitoring_v1_github_actions.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any, Dict, List, Optional, Tuple

import requests
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


# =============================================================================
# Configuration
# =============================================================================

SGT = ZoneInfo("Asia/Singapore")

SIGNAL_V7_TABLE = os.getenv("SIGNAL_V7_TABLE", "ai_stock_signal_scores_v7")
PORTFOLIO_V7_TABLE = os.getenv("PORTFOLIO_V7_TABLE", "ai_portfolio_engine_v7")

RUN_DATE_SGT = os.getenv("RUN_DATE_SGT")
if not RUN_DATE_SGT:
    RUN_DATE_SGT = datetime.now(SGT).date().isoformat()

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "outputs"))

PAGE_SIZE = 1000
TOP_N = 15
SIGNAL_DATE_COL = "run_date_sgt"


# =============================================================================
# Logging and Environment
# =============================================================================

def log(message: str) -> None:
    ts = datetime.now(SGT).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts} SGT] {message}", flush=True)


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value.rstrip("/") if name == "SUPABASE_URL" else value


SUPABASE_URL = require_env("SUPABASE_URL")
SUPABASE_KEY = require_env("SUPABASE_SERVICE_ROLE_KEY")


# =============================================================================
# Supabase REST Helpers
# =============================================================================

def headers() -> Dict[str, str]:
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def table_url(table: str) -> str:
    return f"{SUPABASE_URL}/rest/v1/{table}"


def rest_get(
    table: str,
    params: Optional[Dict[str, str]] = None,
    start: Optional[int] = None,
    end: Optional[int] = None,
    allow_missing_table: bool = False,
) -> List[Dict[str, Any]]:
    request_headers = headers()

    if start is not None and end is not None:
        request_headers["Range-Unit"] = "items"
        request_headers["Range"] = f"{start}-{end}"

    response = requests.get(
        table_url(table),
        headers=request_headers,
        params=params or {},
        timeout=60,
    )

    if response.status_code >= 400:
        txt = response.text.lower()

        if allow_missing_table and (
            "could not find the table" in txt
            or "does not exist" in txt
            or response.status_code == 404
        ):
            log(f"[WARN] Optional table unavailable: {table}")
            return []

        raise RuntimeError(
            f"REST GET failed for table {table}\n"
            f"Status: {response.status_code}\n"
            f"Response: {response.text}"
        )

    return response.json()


def fetch_all(
    table: str,
    params: Optional[Dict[str, str]] = None,
    allow_missing_table: bool = False,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    start = 0

    while True:
        end = start + PAGE_SIZE - 1
        batch = rest_get(
            table,
            params=params,
            start=start,
            end=end,
            allow_missing_table=allow_missing_table,
        )

        rows.extend(batch)

        if len(batch) < PAGE_SIZE:
            break

        start += PAGE_SIZE

    return rows


def latest_available_date(table: str, date_col: str = SIGNAL_DATE_COL) -> Optional[str]:
    rows = rest_get(
        table,
        params={
            "select": date_col,
            "order": f"{date_col}.desc",
            "limit": "1",
        },
        allow_missing_table=True,
    )

    if not rows:
        return None

    return str(rows[0].get(date_col))


# =============================================================================
# Loading
# =============================================================================

def load_table_for_run_date(
    table: str,
    requested_date: str,
    required: bool,
    allow_latest_fallback: bool = True,
) -> Tuple[pd.DataFrame, Optional[str]]:
    log(f"Loading {table} for run_date_sgt={requested_date}")

    rows = fetch_all(
        table,
        params={
            "select": "*",
            SIGNAL_DATE_COL: f"eq.{requested_date}",
        },
        allow_missing_table=not required,
    )

    used_date = requested_date

    if not rows and allow_latest_fallback:
        latest_date = latest_available_date(table)
        if latest_date and latest_date != requested_date:
            log(f"[WARN] No rows for {requested_date} in {table}. Falling back to latest available date: {latest_date}")

            rows = fetch_all(
                table,
                params={
                    "select": "*",
                    SIGNAL_DATE_COL: f"eq.{latest_date}",
                },
                allow_missing_table=not required,
            )

            used_date = latest_date

    if not rows:
        if required:
            raise RuntimeError(f"No rows found in required table {table} for {requested_date}")
        return pd.DataFrame(), None

    df = pd.DataFrame(rows)

    if "ticker" in df.columns:
        df["ticker"] = df["ticker"].astype(str).str.upper().str.strip()

    return df, used_date


def to_numeric(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    out = df.copy()
    for col in cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def normalise_signal_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    numeric_cols = [
        "relative_momentum_score",
        "relative_quality_score",
        "relative_efficiency_score",
        "relative_valuation_score",
        "relative_hype_revision_score",
        "risk_penalty",
        "alpha_score_v7",
        "subsector_rank",
        "global_rank",
    ]

    df = to_numeric(df, numeric_cols)

    if "portfolio_candidate" in df.columns:
        df["portfolio_candidate"] = (
            df["portfolio_candidate"]
            .astype(str)
            .str.lower()
            .isin(["true", "1", "yes"])
        )
    else:
        df["portfolio_candidate"] = False

    return df


def normalise_portfolio_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    numeric_cols = [
        "alpha_score_v7",
        "subsector_rank",
        "global_rank",
        "portfolio_weight",
        "raw_weight",
        "cash_weight",
    ]

    df = to_numeric(df, numeric_cols)

    if "portfolio_weight" not in df.columns and "weight" in df.columns:
        df["portfolio_weight"] = pd.to_numeric(df["weight"], errors="coerce").fillna(0.0)

    if "portfolio_weight" not in df.columns:
        df["portfolio_weight"] = 0.0

    return df


# =============================================================================
# Monitoring Data
# =============================================================================

def build_top_alpha(signal_df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "ticker",
        "company_name",
        "ai_subsector",
        "alpha_score_v7",
        "global_rank",
        "subsector_rank",
        "relative_momentum_score",
        "relative_quality_score",
        "relative_efficiency_score",
        "relative_valuation_score",
        "relative_hype_revision_score",
        "risk_penalty",
        "signal_label",
        "portfolio_candidate",
    ]
    cols = [c for c in cols if c in signal_df.columns]

    return (
        signal_df[cols]
        .sort_values("alpha_score_v7", ascending=False)
        .head(TOP_N)
        .reset_index(drop=True)
    )


def build_subsector_signal_summary(signal_df: pd.DataFrame) -> pd.DataFrame:
    if signal_df.empty or "ai_subsector" not in signal_df.columns:
        return pd.DataFrame()

    summary = (
        signal_df
        .groupby("ai_subsector", dropna=False)
        .agg(
            stock_count=("ticker", "count"),
            avg_alpha_score=("alpha_score_v7", "mean"),
            max_alpha_score=("alpha_score_v7", "max"),
            min_alpha_score=("alpha_score_v7", "min"),
            candidates=("portfolio_candidate", "sum"),
        )
        .reset_index()
    )

    return summary.sort_values("max_alpha_score", ascending=False).round(4)


def build_portfolio_holdings(portfolio_df: pd.DataFrame) -> pd.DataFrame:
    if portfolio_df.empty:
        return pd.DataFrame()

    cols = [
        "ticker",
        "company_name",
        "ai_subsector",
        "portfolio_weight",
        "raw_weight",
        "cash_weight",
        "alpha_score_v7",
        "subsector_rank",
        "global_rank",
        "signal_label",
        "action",
        "source",
    ]
    cols = [c for c in cols if c in portfolio_df.columns]

    return (
        portfolio_df[cols]
        .sort_values("portfolio_weight", ascending=False)
        .reset_index(drop=True)
    )


def build_subsector_weights(portfolio_df: pd.DataFrame) -> pd.DataFrame:
    if portfolio_df.empty or "ai_subsector" not in portfolio_df.columns:
        return pd.DataFrame()

    out = (
        portfolio_df
        .groupby("ai_subsector", dropna=False)
        .agg(
            holdings=("ticker", "count"),
            portfolio_weight=("portfolio_weight", "sum"),
            avg_alpha_score=("alpha_score_v7", "mean"),
        )
        .reset_index()
        .sort_values("portfolio_weight", ascending=False)
    )

    return out.round(6)


def build_summary(
    signal_df: pd.DataFrame,
    portfolio_df: pd.DataFrame,
    signal_date_used: Optional[str],
    portfolio_date_used: Optional[str],
) -> pd.DataFrame:
    total_signal_rows = len(signal_df)
    total_portfolio_rows = len(portfolio_df)

    equity_df = portfolio_df.copy()
    if not equity_df.empty and "ticker" in equity_df.columns:
        equity_df = equity_df[equity_df["ticker"] != "CASH"]

    cash_weight = 0.0
    if not portfolio_df.empty and "ticker" in portfolio_df.columns:
        cash_rows = portfolio_df[portfolio_df["ticker"] == "CASH"]
        if not cash_rows.empty and "portfolio_weight" in cash_rows.columns:
            cash_weight = float(cash_rows["portfolio_weight"].fillna(0).sum())

    total_weight = 0.0
    if not portfolio_df.empty and "portfolio_weight" in portfolio_df.columns:
        total_weight = float(portfolio_df["portfolio_weight"].fillna(0).sum())

    avg_alpha_all = None
    max_alpha_all = None
    min_alpha_all = None

    if not signal_df.empty and "alpha_score_v7" in signal_df.columns:
        avg_alpha_all = float(signal_df["alpha_score_v7"].mean())
        max_alpha_all = float(signal_df["alpha_score_v7"].max())
        min_alpha_all = float(signal_df["alpha_score_v7"].min())

    avg_alpha_portfolio = None
    if not equity_df.empty and "alpha_score_v7" in equity_df.columns:
        avg_alpha_portfolio = float(equity_df["alpha_score_v7"].mean())

    top_alpha_ticker = None
    if not signal_df.empty and "alpha_score_v7" in signal_df.columns:
        top_row = signal_df.sort_values("alpha_score_v7", ascending=False).iloc[0]
        top_alpha_ticker = top_row.get("ticker")

    return pd.DataFrame([{
        "run_date_sgt_requested": RUN_DATE_SGT,
        "signal_date_used": signal_date_used,
        "portfolio_date_used": portfolio_date_used,
        "signal_rows": total_signal_rows,
        "portfolio_rows": total_portfolio_rows,
        "equity_holdings": len(equity_df),
        "subsectors_in_signal_universe": None if signal_df.empty or "ai_subsector" not in signal_df.columns else int(signal_df["ai_subsector"].nunique()),
        "subsectors_in_portfolio": None if equity_df.empty or "ai_subsector" not in equity_df.columns else int(equity_df["ai_subsector"].nunique()),
        "total_portfolio_weight": round(total_weight, 6),
        "cash_weight": round(cash_weight, 6),
        "equity_weight": round(total_weight - cash_weight, 6),
        "avg_alpha_all": None if avg_alpha_all is None else round(avg_alpha_all, 4),
        "max_alpha_all": None if max_alpha_all is None else round(max_alpha_all, 4),
        "min_alpha_all": None if min_alpha_all is None else round(min_alpha_all, 4),
        "avg_alpha_portfolio": None if avg_alpha_portfolio is None else round(avg_alpha_portfolio, 4),
        "top_alpha_ticker": top_alpha_ticker,
        "generated_at_sgt": datetime.now(SGT).isoformat(),
        "status": "OK",
    }])


# =============================================================================
# Charts
# =============================================================================

def save_bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    output_path: Path,
    top_n: int = 15,
    ascending: bool = False,
) -> Optional[str]:
    if df.empty or x not in df.columns or y not in df.columns:
        return None

    chart_df = df[[x, y]].copy()
    chart_df[y] = pd.to_numeric(chart_df[y], errors="coerce")
    chart_df = chart_df.dropna(subset=[y]).sort_values(y, ascending=ascending).head(top_n)

    if chart_df.empty:
        return None

    plt.figure(figsize=(11, 5.5))
    plt.bar(chart_df[x].astype(str), chart_df[y])
    plt.title(title)
    plt.xlabel(x)
    plt.ylabel(y)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=140)
    plt.close()

    return output_path.name


def save_histogram(
    df: pd.DataFrame,
    col: str,
    title: str,
    output_path: Path,
) -> Optional[str]:
    if df.empty or col not in df.columns:
        return None

    values = pd.to_numeric(df[col], errors="coerce").dropna()

    if values.empty:
        return None

    plt.figure(figsize=(9, 5))
    plt.hist(values, bins=15)
    plt.title(title)
    plt.xlabel(col)
    plt.ylabel("count")
    plt.tight_layout()
    plt.savefig(output_path, dpi=140)
    plt.close()

    return output_path.name


def save_scatter_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    label_col: str,
    title: str,
    output_path: Path,
) -> Optional[str]:
    if df.empty or x not in df.columns or y not in df.columns or label_col not in df.columns:
        return None

    chart_df = df[[x, y, label_col]].copy()
    chart_df[x] = pd.to_numeric(chart_df[x], errors="coerce")
    chart_df[y] = pd.to_numeric(chart_df[y], errors="coerce")
    chart_df = chart_df.dropna(subset=[x, y])

    if chart_df.empty:
        return None

    plt.figure(figsize=(8.5, 6))
    plt.scatter(chart_df[x], chart_df[y])

    for _, row in chart_df.iterrows():
        plt.annotate(str(row[label_col]), (row[x], row[y]), fontsize=8)

    plt.title(title)
    plt.xlabel(x)
    plt.ylabel(y)
    plt.tight_layout()
    plt.savefig(output_path, dpi=140)
    plt.close()

    return output_path.name


def generate_charts(
    signal_df: pd.DataFrame,
    portfolio_holdings: pd.DataFrame,
    subsector_weights: pd.DataFrame,
    stamp: str,
) -> List[str]:
    chart_files: List[str] = []

    candidates = [
        save_bar_chart(
            signal_df,
            "ticker",
            "alpha_score_v7",
            "Top v7 Alpha Scores",
            OUTPUT_DIR / f"chart_top_alpha_scores_{stamp}.png",
            top_n=15,
            ascending=False,
        ),
        save_histogram(
            signal_df,
            "alpha_score_v7",
            "Distribution of v7 Alpha Scores",
            OUTPUT_DIR / f"chart_alpha_score_distribution_{stamp}.png",
        ),
        save_bar_chart(
            portfolio_holdings,
            "ticker",
            "portfolio_weight",
            "Portfolio Weights",
            OUTPUT_DIR / f"chart_portfolio_weights_{stamp}.png",
            top_n=20,
            ascending=False,
        ),
        save_bar_chart(
            subsector_weights,
            "ai_subsector",
            "portfolio_weight",
            "Subsector Weights",
            OUTPUT_DIR / f"chart_subsector_weights_{stamp}.png",
            top_n=20,
            ascending=False,
        ),
        save_scatter_chart(
            signal_df,
            "relative_momentum_score",
            "alpha_score_v7",
            "ticker",
            "Relative Momentum vs v7 Alpha Score",
            OUTPUT_DIR / f"chart_momentum_vs_alpha_{stamp}.png",
        ),
    ]

    for chart in candidates:
        if chart:
            chart_files.append(chart)

    return chart_files


# =============================================================================
# HTML Report
# =============================================================================

def html_table(df: pd.DataFrame, max_rows: int = 30) -> str:
    if df.empty:
        return "<p><em>No rows.</em></p>"

    show = df.head(max_rows).copy()

    for col in show.columns:
        if pd.api.types.is_numeric_dtype(show[col]):
            show[col] = show[col].round(4)

    return show.to_html(index=False, escape=False, border=0, classes="data-table")


def build_html_report(
    summary: pd.DataFrame,
    top_alpha: pd.DataFrame,
    portfolio_holdings: pd.DataFrame,
    subsector_weights: pd.DataFrame,
    subsector_signal_summary: pd.DataFrame,
    chart_files: List[str],
    output_path: Path,
) -> None:
    s = summary.iloc[0].to_dict()

    chart_html = ""
    for file in chart_files:
        chart_html += f'<div class="chart"><img src="{file}" /></div>\n'

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>AI Portfolio v7 Monitoring Report - {s.get("run_date_sgt_requested")}</title>
<style>
body {{
    font-family: Arial, sans-serif;
    margin: 28px;
    color: #222;
    background: #fafafa;
}}
h1, h2 {{ color: #111; }}
.kpi-grid {{
    display: grid;
    grid-template-columns: repeat(4, minmax(160px, 1fr));
    gap: 12px;
    margin-bottom: 24px;
}}
.kpi {{
    background: white;
    border: 1px solid #ddd;
    border-radius: 10px;
    padding: 14px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}}
.kpi-label {{
    color: #666;
    font-size: 12px;
    margin-bottom: 6px;
}}
.kpi-value {{
    font-size: 22px;
    font-weight: bold;
}}
.section {{
    background: white;
    border: 1px solid #ddd;
    border-radius: 10px;
    padding: 18px;
    margin-bottom: 22px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}}
.data-table {{
    border-collapse: collapse;
    width: 100%;
    font-size: 13px;
}}
.data-table th {{
    background: #f0f0f0;
    text-align: left;
    padding: 8px;
    border-bottom: 1px solid #ccc;
}}
.data-table td {{
    padding: 7px;
    border-bottom: 1px solid #eee;
}}
.chart img {{
    max-width: 100%;
    margin: 10px 0 18px 0;
    border: 1px solid #ddd;
    border-radius: 8px;
}}
.note {{
    color: #555;
    font-size: 13px;
}}
</style>
</head>
<body>
<h1>AI Portfolio v7 Monitoring Report</h1>
<p class="note">
Requested run date: <strong>{s.get("run_date_sgt_requested")}</strong><br>
Signal date used: <strong>{s.get("signal_date_used")}</strong><br>
Portfolio date used: <strong>{s.get("portfolio_date_used")}</strong><br>
Generated at: <strong>{s.get("generated_at_sgt")}</strong>
</p>

<div class="kpi-grid">
    <div class="kpi"><div class="kpi-label">Signal Rows</div><div class="kpi-value">{s.get("signal_rows")}</div></div>
    <div class="kpi"><div class="kpi-label">Equity Holdings</div><div class="kpi-value">{s.get("equity_holdings")}</div></div>
    <div class="kpi"><div class="kpi-label">Portfolio Subsectors</div><div class="kpi-value">{s.get("subsectors_in_portfolio")}</div></div>
    <div class="kpi"><div class="kpi-label">Cash Weight</div><div class="kpi-value">{s.get("cash_weight")}</div></div>
    <div class="kpi"><div class="kpi-label">Total Weight</div><div class="kpi-value">{s.get("total_portfolio_weight")}</div></div>
    <div class="kpi"><div class="kpi-label">Avg Alpha All</div><div class="kpi-value">{s.get("avg_alpha_all")}</div></div>
    <div class="kpi"><div class="kpi-label">Avg Alpha Portfolio</div><div class="kpi-value">{s.get("avg_alpha_portfolio")}</div></div>
    <div class="kpi"><div class="kpi-label">Top Alpha Ticker</div><div class="kpi-value">{s.get("top_alpha_ticker")}</div></div>
</div>

<div class="section">
<h2>Charts</h2>
{chart_html if chart_html else "<p><em>No charts generated.</em></p>"}
</div>

<div class="section">
<h2>Portfolio Holdings</h2>
{html_table(portfolio_holdings, 30)}
</div>

<div class="section">
<h2>Subsector Portfolio Weights</h2>
{html_table(subsector_weights, 30)}
</div>

<div class="section">
<h2>Top v7 Alpha Candidates</h2>
{html_table(top_alpha, TOP_N)}
</div>

<div class="section">
<h2>Subsector Signal Summary</h2>
{html_table(subsector_signal_summary, 50)}
</div>

<div class="section">
<h2>Production Summary</h2>
{html_table(summary, 5)}
</div>

</body>
</html>
"""

    output_path.write_text(html, encoding="utf-8")


# =============================================================================
# Validation
# =============================================================================

def validate_outputs(summary: pd.DataFrame, portfolio_df: pd.DataFrame) -> None:
    s = summary.iloc[0]

    if int(s["signal_rows"]) <= 0:
        raise RuntimeError("Validation failed: no signal rows found.")

    if int(s["portfolio_rows"]) <= 0:
        raise RuntimeError("Validation failed: no portfolio rows found.")

    total_weight = float(s["total_portfolio_weight"])

    if total_weight < 0.95 or total_weight > 1.05:
        raise RuntimeError(
            f"Validation failed: total portfolio weight is {total_weight:.4f}, expected close to 1.0."
        )

    if not portfolio_df.empty and "portfolio_weight" in portfolio_df.columns:
        if portfolio_df["portfolio_weight"].isna().any():
            raise RuntimeError("Validation failed: portfolio contains null weights.")


# =============================================================================
# Main
# =============================================================================

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    stamp = RUN_DATE_SGT.replace("-", "")

    log("=" * 90)
    log("AI PORTFOLIO MONITORING v1 - GITHUB ACTIONS READY")
    log("=" * 90)
    log(f"Requested run date : {RUN_DATE_SGT}")
    log(f"Signal table       : {SIGNAL_V7_TABLE}")
    log(f"Portfolio table    : {PORTFOLIO_V7_TABLE}")
    log(f"Output directory   : {OUTPUT_DIR.resolve()}")
    log("-" * 90)

    signal_df, signal_date_used = load_table_for_run_date(
        SIGNAL_V7_TABLE,
        RUN_DATE_SGT,
        required=True,
        allow_latest_fallback=True,
    )
    portfolio_df, portfolio_date_used = load_table_for_run_date(
        PORTFOLIO_V7_TABLE,
        RUN_DATE_SGT,
        required=True,
        allow_latest_fallback=True,
    )

    signal_df = normalise_signal_df(signal_df)
    portfolio_df = normalise_portfolio_df(portfolio_df)

    top_alpha = build_top_alpha(signal_df)
    portfolio_holdings = build_portfolio_holdings(portfolio_df)
    subsector_weights = build_subsector_weights(portfolio_df)
    subsector_signal_summary = build_subsector_signal_summary(signal_df)
    summary = build_summary(signal_df, portfolio_df, signal_date_used, portfolio_date_used)

    validate_outputs(summary, portfolio_df)

    # File paths
    summary_path = OUTPUT_DIR / f"ai_portfolio_v7_summary_{stamp}.csv"
    signal_path = OUTPUT_DIR / f"ai_portfolio_v7_signal_scores_{stamp}.csv"
    top_alpha_path = OUTPUT_DIR / f"ai_portfolio_v7_top_alpha_{stamp}.csv"
    holdings_path = OUTPUT_DIR / f"ai_portfolio_v7_holdings_{stamp}.csv"
    subsector_weights_path = OUTPUT_DIR / f"ai_portfolio_v7_subsector_weights_{stamp}.csv"
    subsector_signal_path = OUTPUT_DIR / f"ai_portfolio_v7_subsector_signal_summary_{stamp}.csv"
    html_path = OUTPUT_DIR / f"ai_portfolio_v7_monitor_report_{stamp}.html"

    # Save CSVs
    summary.to_csv(summary_path, index=False)
    signal_df.to_csv(signal_path, index=False)
    top_alpha.to_csv(top_alpha_path, index=False)
    portfolio_holdings.to_csv(holdings_path, index=False)
    subsector_weights.to_csv(subsector_weights_path, index=False)
    subsector_signal_summary.to_csv(subsector_signal_path, index=False)

    # Charts and HTML
    chart_files = generate_charts(signal_df, portfolio_holdings, subsector_weights, stamp)

    build_html_report(
        summary,
        top_alpha,
        portfolio_holdings,
        subsector_weights,
        subsector_signal_summary,
        chart_files,
        html_path,
    )

    log("Generated files:")
    log(f"  HTML report              : {html_path}")
    log(f"  Summary CSV              : {summary_path}")
    log(f"  Signal scores CSV        : {signal_path}")
    log(f"  Top alpha CSV            : {top_alpha_path}")
    log(f"  Portfolio holdings CSV   : {holdings_path}")
    log(f"  Subsector weights CSV    : {subsector_weights_path}")
    log(f"  Subsector signal CSV     : {subsector_signal_path}")

    if chart_files:
        log("  Charts:")
        for chart in chart_files:
            log(f"    - {OUTPUT_DIR / chart}")
    else:
        log("  Charts: none generated")

    log("-" * 90)
    log("Production summary:")
    print(summary.to_string(index=False), flush=True)
    log("=" * 90)
    log("[DONE] Monitoring complete.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("\nERROR", flush=True)
        print("=" * 90, flush=True)
        print(str(exc), flush=True)
        print("=" * 90, flush=True)
        sys.exit(1)
