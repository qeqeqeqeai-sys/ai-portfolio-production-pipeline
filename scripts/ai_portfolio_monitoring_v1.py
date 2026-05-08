#!/usr/bin/env python3
"""
AI Signal v5 Monitoring Script v1

Reads ai_stock_signal_scores_v5 via Supabase REST API and produces:
- HTML monitoring report
- CSV summary
- CSV rank changes
- CSV crowded trades
- CSV top signals
- Optional portfolio impact CSV if portfolio table exists

No Supabase Python module required.

Install:
    pip install pandas numpy requests python-dotenv matplotlib

Required .env:
    SUPABASE_URL=...
    SUPABASE_SERVICE_ROLE_KEY=...

Optional .env:
    RUN_DATE_SGT=YYYY-MM-DD
    SIGNAL_V5_TABLE=ai_stock_signal_scores_v5
    PORTFOLIO_TABLE=ai_portfolio_positions
    OUTPUT_DIR=monitor_reports
"""

from __future__ import annotations

import os
import sys
import math
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


SIGNAL_V5_TABLE = os.getenv("SIGNAL_V5_TABLE", "ai_stock_signal_scores_v5")
PORTFOLIO_TABLE = os.getenv("PORTFOLIO_TABLE", "ai_portfolio_positions")
RUN_DATE_SGT = os.getenv("RUN_DATE_SGT")
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "monitor_reports"))

SIGNAL_DATE_COL = "run_date_sgt"
PAGE_SIZE = 1000
TOP_N = 10


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value.rstrip("/") if name == "SUPABASE_URL" else value


SUPABASE_URL = require_env("SUPABASE_URL")
SUPABASE_KEY = require_env("SUPABASE_SERVICE_ROLE_KEY")


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
    h = headers()
    if start is not None and end is not None:
        h["Range-Unit"] = "items"
        h["Range"] = f"{start}-{end}"

    r = requests.get(table_url(table), headers=h, params=params or {}, timeout=60)

    if r.status_code >= 400:
        txt = r.text.lower()
        if allow_missing_table and (
            "could not find the table" in txt
            or "does not exist" in txt
            or r.status_code == 404
        ):
            return []
        raise RuntimeError(
            f"REST GET failed for table {table}\n"
            f"Status: {r.status_code}\n"
            f"Response: {r.text}"
        )

    return r.json()


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


def latest_date(table: str, date_col: str) -> str:
    rows = rest_get(
        table,
        params={
            "select": date_col,
            "order": f"{date_col}.desc",
            "limit": "1",
        },
    )
    if not rows:
        raise RuntimeError(f"No rows found in {table}")
    return rows[0][date_col]


def resolve_run_date() -> str:
    if RUN_DATE_SGT:
        return RUN_DATE_SGT
    return latest_date(SIGNAL_V5_TABLE, SIGNAL_DATE_COL)


def to_numeric(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def load_signal_v5(run_date: str) -> pd.DataFrame:
    rows = fetch_all(
        SIGNAL_V5_TABLE,
        params={
            "select": "*",
            SIGNAL_DATE_COL: f"eq.{run_date}",
        },
    )

    if not rows:
        raise RuntimeError(f"No rows found in {SIGNAL_V5_TABLE} for {run_date}")

    df = pd.DataFrame(rows)
    df["ticker"] = df["ticker"].astype(str).str.upper().str.strip()

    numeric_cols = [
        "momentum_score",
        "valuation_score",
        "risk_overheating_score",
        "composite_score",
        "rank_overall",
        "rank_risk",
        "hype_score",
        "hype_excess",
        "hype_risk_bump",
        "hype_composite_penalty",
        "risk_overheating_score_v47",
        "composite_score_v47",
    ]
    df = to_numeric(df, numeric_cols)

    for col in ["crowded_trade_flag", "extreme_hype_flag"]:
        if col in df.columns:
            df[col] = df[col].fillna(False).astype(bool)
        else:
            df[col] = False

    for col in ["hype_score", "hype_composite_penalty", "hype_risk_bump"]:
        if col not in df.columns:
            df[col] = 0.0

    return df


def load_portfolio(run_date: str) -> pd.DataFrame:
    rows = fetch_all(
        PORTFOLIO_TABLE,
        params={
            "select": "*",
            SIGNAL_DATE_COL: f"eq.{run_date}",
        },
        allow_missing_table=True,
    )

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    if "ticker" not in df.columns:
        return pd.DataFrame()

    df["ticker"] = df["ticker"].astype(str).str.upper().str.strip()

    if "weight" in df.columns:
        df["weight"] = pd.to_numeric(df["weight"], errors="coerce").fillna(0.0)
    else:
        df["weight"] = 0.0

    return df


def build_rank_changes(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    if "composite_score_v47" not in out.columns:
        out["composite_score_v47"] = np.nan
    if "risk_overheating_score_v47" not in out.columns:
        out["risk_overheating_score_v47"] = np.nan

    out["rank_v47_est"] = out["composite_score_v47"].rank(method="dense", ascending=False)
    out["rank_v5"] = out["composite_score"].rank(method="dense", ascending=False)
    out["rank_change"] = out["rank_v47_est"] - out["rank_v5"]
    out["composite_change"] = out["composite_score"] - out["composite_score_v47"]
    out["risk_change"] = out["risk_overheating_score"] - out["risk_overheating_score_v47"]

    cols = [
        "ticker",
        "rank_v47_est",
        "rank_v5",
        "rank_change",
        "composite_score_v47",
        "composite_score",
        "composite_change",
        "risk_overheating_score_v47",
        "risk_overheating_score",
        "risk_change",
        "hype_score",
        "hype_composite_penalty",
        "hype_risk_bump",
        "crowded_trade_flag",
        "signal_label",
    ]
    cols = [c for c in cols if c in out.columns]

    return (
        out[cols]
        .sort_values(["hype_composite_penalty", "hype_score"], ascending=[False, False])
        .reset_index(drop=True)
    )


def build_crowded(df: pd.DataFrame) -> pd.DataFrame:
    out = df[df["crowded_trade_flag"] == True].copy()

    cols = [
        "ticker",
        "composite_score",
        "risk_overheating_score",
        "hype_score",
        "hype_regime",
        "hype_composite_penalty",
        "hype_risk_bump",
        "extreme_hype_flag",
        "signal_label",
    ]
    cols = [c for c in cols if c in out.columns]

    return (
        out[cols]
        .sort_values(["hype_score", "risk_overheating_score"], ascending=[False, False])
        .reset_index(drop=True)
    )


def build_top_signals(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "ticker",
        "rank_overall",
        "composite_score",
        "composite_score_v47",
        "hype_score",
        "hype_composite_penalty",
        "risk_overheating_score",
        "crowded_trade_flag",
        "signal_label",
    ]
    cols = [c for c in cols if c in df.columns]

    return (
        df[cols]
        .sort_values("composite_score", ascending=False)
        .head(TOP_N)
        .reset_index(drop=True)
    )


def build_portfolio_impact(signal_df: pd.DataFrame, portfolio_df: pd.DataFrame) -> pd.DataFrame:
    if portfolio_df.empty:
        return pd.DataFrame()

    merged = portfolio_df.merge(
        signal_df,
        on="ticker",
        how="left",
        suffixes=("_portfolio", "_signal"),
    )

    if "weight" not in merged.columns:
        merged["weight"] = 0.0

    merged["weighted_hype"] = merged["weight"] * merged["hype_score"].fillna(0.0)
    merged["weighted_penalty"] = merged["weight"] * merged["hype_composite_penalty"].fillna(0.0)

    cols = [
        "ticker",
        "weight",
        "action",
        "composite_score",
        "hype_score",
        "hype_regime",
        "hype_composite_penalty",
        "risk_overheating_score",
        "crowded_trade_flag",
        "signal_label_signal",
        "signal_label_portfolio",
        "weighted_hype",
        "weighted_penalty",
    ]
    cols = [c for c in cols if c in merged.columns]

    return merged[cols].sort_values("weight", ascending=False).reset_index(drop=True)


def build_summary(signal_df: pd.DataFrame, portfolio_impact: pd.DataFrame, run_date: str) -> pd.DataFrame:
    total = len(signal_df)
    crowded_count = int(signal_df["crowded_trade_flag"].sum())
    extreme_count = int(signal_df["extreme_hype_flag"].sum())

    top_hype_ticker = None
    top_penalty_ticker = None
    if total > 0:
        top_hype_ticker = signal_df.sort_values("hype_score", ascending=False).iloc[0]["ticker"]
        top_penalty_ticker = signal_df.sort_values("hype_composite_penalty", ascending=False).iloc[0]["ticker"]

    portfolio_crowded_count = None
    portfolio_weighted_hype = None
    portfolio_weighted_penalty = None

    if not portfolio_impact.empty:
        if "crowded_trade_flag" in portfolio_impact.columns:
            portfolio_crowded_count = int(portfolio_impact["crowded_trade_flag"].fillna(False).sum())
        if "weighted_hype" in portfolio_impact.columns:
            portfolio_weighted_hype = float(portfolio_impact["weighted_hype"].fillna(0).sum())
        if "weighted_penalty" in portfolio_impact.columns:
            portfolio_weighted_penalty = float(portfolio_impact["weighted_penalty"].fillna(0).sum())

    return pd.DataFrame([{
        "run_date_sgt": run_date,
        "total_names": total,
        "crowded_trade_count": crowded_count,
        "extreme_hype_count": extreme_count,
        "avg_hype_score": round(float(signal_df["hype_score"].fillna(0).mean()), 4),
        "max_hype_score": round(float(signal_df["hype_score"].fillna(0).max()), 4),
        "avg_hype_composite_penalty": round(float(signal_df["hype_composite_penalty"].fillna(0).mean()), 4),
        "max_hype_composite_penalty": round(float(signal_df["hype_composite_penalty"].fillna(0).max()), 4),
        "avg_hype_risk_bump": round(float(signal_df["hype_risk_bump"].fillna(0).mean()), 4),
        "max_hype_risk_bump": round(float(signal_df["hype_risk_bump"].fillna(0).max()), 4),
        "top_hype_ticker": top_hype_ticker,
        "top_penalty_ticker": top_penalty_ticker,
        "portfolio_rows": len(portfolio_impact),
        "portfolio_crowded_count": portfolio_crowded_count,
        "portfolio_weighted_hype": None if portfolio_weighted_hype is None else round(portfolio_weighted_hype, 4),
        "portfolio_weighted_penalty": None if portfolio_weighted_penalty is None else round(portfolio_weighted_penalty, 4),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }])


def save_bar_chart(df: pd.DataFrame, x: str, y: str, title: str, output_path: Path, top_n: int = 15) -> Optional[str]:
    if df.empty or x not in df.columns or y not in df.columns:
        return None

    chart_df = df[[x, y]].copy()
    chart_df[y] = pd.to_numeric(chart_df[y], errors="coerce")
    chart_df = chart_df.dropna(subset=[y]).sort_values(y, ascending=False).head(top_n)

    if chart_df.empty:
        return None

    plt.figure(figsize=(10, 5))
    plt.bar(chart_df[x].astype(str), chart_df[y])
    plt.title(title)
    plt.xlabel(x)
    plt.ylabel(y)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=140)
    plt.close()
    return output_path.name


def save_scatter_chart(df: pd.DataFrame, x: str, y: str, title: str, output_path: Path) -> Optional[str]:
    if df.empty or x not in df.columns or y not in df.columns:
        return None

    chart_df = df[[x, y, "ticker"]].copy()
    chart_df[x] = pd.to_numeric(chart_df[x], errors="coerce")
    chart_df[y] = pd.to_numeric(chart_df[y], errors="coerce")
    chart_df = chart_df.dropna(subset=[x, y])

    if chart_df.empty:
        return None

    plt.figure(figsize=(8, 6))
    plt.scatter(chart_df[x], chart_df[y])

    for _, row in chart_df.iterrows():
        plt.annotate(str(row["ticker"]), (row[x], row[y]), fontsize=8)

    plt.title(title)
    plt.xlabel(x)
    plt.ylabel(y)
    plt.tight_layout()
    plt.savefig(output_path, dpi=140)
    plt.close()
    return output_path.name


def html_table(df: pd.DataFrame, max_rows: int = 20) -> str:
    if df.empty:
        return "<p><em>No rows.</em></p>"

    show = df.head(max_rows).copy()

    for col in show.columns:
        if pd.api.types.is_numeric_dtype(show[col]):
            show[col] = show[col].round(4)

    return show.to_html(index=False, escape=False, border=0, classes="data-table")


def build_html(
    run_date: str,
    summary: pd.DataFrame,
    top: pd.DataFrame,
    rank_changes: pd.DataFrame,
    crowded: pd.DataFrame,
    portfolio_impact: pd.DataFrame,
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
<title>AI Signal v5 Monitoring Report - {run_date}</title>
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
<h1>AI Signal v5 Monitoring Report</h1>
<p class="note">Run date: <strong>{run_date}</strong></p>

<div class="kpi-grid">
    <div class="kpi"><div class="kpi-label">Total Names</div><div class="kpi-value">{s.get("total_names")}</div></div>
    <div class="kpi"><div class="kpi-label">Crowded Trades</div><div class="kpi-value">{s.get("crowded_trade_count")}</div></div>
    <div class="kpi"><div class="kpi-label">Extreme Hype</div><div class="kpi-value">{s.get("extreme_hype_count")}</div></div>
    <div class="kpi"><div class="kpi-label">Avg Hype Score</div><div class="kpi-value">{s.get("avg_hype_score")}</div></div>
    <div class="kpi"><div class="kpi-label">Max Hype Score</div><div class="kpi-value">{s.get("max_hype_score")}</div></div>
    <div class="kpi"><div class="kpi-label">Max Penalty</div><div class="kpi-value">{s.get("max_hype_composite_penalty")}</div></div>
    <div class="kpi"><div class="kpi-label">Top Hype Ticker</div><div class="kpi-value">{s.get("top_hype_ticker")}</div></div>
    <div class="kpi"><div class="kpi-label">Top Penalty Ticker</div><div class="kpi-value">{s.get("top_penalty_ticker")}</div></div>
</div>

<div class="section">
<h2>Charts</h2>
{chart_html if chart_html else "<p><em>No charts generated.</em></p>"}
</div>

<div class="section">
<h2>Top {TOP_N} v5 Signals</h2>
{html_table(top, TOP_N)}
</div>

<div class="section">
<h2>Crowded Trades</h2>
{html_table(crowded, 30)}
</div>

<div class="section">
<h2>Biggest Hype Penalties / Rank Changes</h2>
{html_table(rank_changes, 30)}
</div>

<div class="section">
<h2>Portfolio Impact</h2>
<p class="note">Appears if matching portfolio rows are found.</p>
{html_table(portfolio_impact, 30)}
</div>

<div class="section">
<h2>Summary Table</h2>
{html_table(summary, 5)}
</div>

</body>
</html>
"""
    output_path.write_text(html, encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    run_date = resolve_run_date()
    stamp = run_date.replace("-", "")

    print("=" * 90)
    print("AI SIGNAL v5 MONITORING SCRIPT v1")
    print("=" * 90)
    print(f"Run date     : {run_date}")
    print(f"Signal table : {SIGNAL_V5_TABLE}")
    print(f"Portfolio tbl: {PORTFOLIO_TABLE}")
    print(f"Output dir   : {OUTPUT_DIR.resolve()}")
    print("-" * 90)

    signal_df = load_signal_v5(run_date)
    portfolio_df = load_portfolio(run_date)

    rank_changes = build_rank_changes(signal_df)
    crowded = build_crowded(signal_df)
    top = build_top_signals(signal_df)
    portfolio_impact = build_portfolio_impact(signal_df, portfolio_df)
    summary = build_summary(signal_df, portfolio_impact, run_date)

    summary_path = OUTPUT_DIR / f"ai_signal_v5_summary_{stamp}.csv"
    rank_path = OUTPUT_DIR / f"ai_signal_v5_rank_changes_{stamp}.csv"
    crowded_path = OUTPUT_DIR / f"ai_signal_v5_crowded_trades_{stamp}.csv"
    top_path = OUTPUT_DIR / f"ai_signal_v5_top_signals_{stamp}.csv"
    portfolio_path = OUTPUT_DIR / f"ai_signal_v5_portfolio_impact_{stamp}.csv"
    html_path = OUTPUT_DIR / f"ai_signal_v5_monitor_report_{stamp}.html"

    summary.to_csv(summary_path, index=False)
    rank_changes.to_csv(rank_path, index=False)
    crowded.to_csv(crowded_path, index=False)
    top.to_csv(top_path, index=False)

    if not portfolio_impact.empty:
        portfolio_impact.to_csv(portfolio_path, index=False)

    chart_files: List[str] = []

    for chart in [
        save_bar_chart(signal_df, "ticker", "hype_score", "Top Hype Scores", OUTPUT_DIR / f"chart_top_hype_{stamp}.png", 15),
        save_bar_chart(signal_df, "ticker", "hype_composite_penalty", "Top Hype Composite Penalties", OUTPUT_DIR / f"chart_top_hype_penalties_{stamp}.png", 15),
        save_scatter_chart(signal_df, "hype_score", "composite_score", "Hype Score vs v5 Composite Score", OUTPUT_DIR / f"chart_hype_vs_composite_{stamp}.png"),
    ]:
        if chart:
            chart_files.append(chart)

    build_html(
        run_date,
        summary,
        top,
        rank_changes,
        crowded,
        portfolio_impact,
        chart_files,
        html_path,
    )

    print("Generated files:")
    print(f"  HTML report        : {html_path}")
    print(f"  Summary CSV        : {summary_path}")
    print(f"  Rank changes CSV   : {rank_path}")
    print(f"  Crowded trades CSV : {crowded_path}")
    print(f"  Top signals CSV    : {top_path}")

    if not portfolio_impact.empty:
        print(f"  Portfolio impact   : {portfolio_path}")
    else:
        print("  Portfolio impact   : skipped, no matching portfolio rows/table found")

    print("-" * 90)
    print("Summary:")
    print(summary.to_string(index=False))
    print("=" * 90)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("\nERROR")
        print("=" * 90)
        print(str(exc))
        print("=" * 90)
        sys.exit(1)
