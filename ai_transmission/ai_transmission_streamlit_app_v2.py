#!/usr/bin/env python3
"""
ai_transmission_streamlit_app_v2.py

Phase 1 Streamlit refactor:
- Queries generic structural_theme_scores table
- Supports theme_name filtering
- Uses latest run_date_sgt automatically
- Adds summary cards
- Adds sector/subsector views
- Keeps architecture ready for future themes:
  ai, energy_demand, ai_energy_interaction, etc.

Required Streamlit secrets:
SUPABASE_URL
SUPABASE_ANON_KEY

Optional:
DEFAULT_THEME
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Structural Theme Transmission Dashboard",
    page_icon="📡",
    layout="wide",
)


# ============================================================
# CONFIG
# ============================================================

TABLE_NAME = "structural_theme_scores"

DEFAULT_THEME = st.secrets.get("DEFAULT_THEME", "ai")

AVAILABLE_THEMES = [
    "ai",
    "energy_demand",
    "ai_energy_interaction",
    "geopolitics",
    "cybersecurity",
    "automation",
    "ageing",
]


# ============================================================
# SUPABASE HELPERS
# ============================================================

def get_supabase_config() -> tuple[str, str]:
    supabase_url = st.secrets.get("SUPABASE_URL", "").rstrip("/")
    supabase_key = st.secrets.get("SUPABASE_ANON_KEY", "")

    if not supabase_url:
        st.error("Missing SUPABASE_URL in Streamlit secrets.")
        st.stop()

    if not supabase_key:
        st.error("Missing SUPABASE_ANON_KEY in Streamlit secrets.")
        st.stop()

    return supabase_url, supabase_key


def supabase_headers() -> Dict[str, str]:
    _, key = get_supabase_config()

    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    }


def supabase_get(
    table: str,
    params: Dict[str, str],
) -> List[Dict[str, Any]]:
    supabase_url, _ = get_supabase_config()

    url = f"{supabase_url}/rest/v1/{table}"

    response = requests.get(
        url,
        headers=supabase_headers(),
        params=params,
        timeout=45,
    )

    if response.status_code >= 400:
        st.error(f"Supabase query failed: HTTP {response.status_code}")
        st.code(response.text)
        st.stop()

    return response.json()


# ============================================================
# DATA ACCESS LAYER
# ============================================================

@st.cache_data(ttl=300)
def load_available_theme_summary() -> pd.DataFrame:
    rows = supabase_get(
        TABLE_NAME,
        params={
            "select": "theme_name,run_date_sgt,ticker,theme_score,confidence_score",
            "limit": "5000",
        },
    )

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    summary = (
        df.groupby("theme_name", as_index=False)
        .agg(
            rows=("ticker", "count"),
            latest_run_date=("run_date_sgt", "max"),
            avg_theme_score=("theme_score", "mean"),
            avg_confidence_score=("confidence_score", "mean"),
        )
        .sort_values("theme_name")
    )

    return summary


@st.cache_data(ttl=300)
def load_theme_scores(
    theme_name: str,
    run_date_sgt: Optional[str] = None,
    limit: int = 1000,
) -> pd.DataFrame:

    params = {
        "select": "*",
        "theme_name": f"eq.{theme_name}",
        "order": "run_date_sgt.desc,theme_score.desc",
        "limit": str(limit),
    }

    if run_date_sgt:
        params["run_date_sgt"] = f"eq.{run_date_sgt}"

    rows = supabase_get(TABLE_NAME, params=params)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    numeric_cols = [
        "theme_score",
        "confidence_score",
        "interaction_score",
        "evidence_count",
        "positive_driver_count",
        "negative_driver_count",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def get_latest_run_date(df: pd.DataFrame) -> Optional[str]:
    if df.empty or "run_date_sgt" not in df.columns:
        return None

    return str(df["run_date_sgt"].max())


# ============================================================
# UI HELPERS
# ============================================================

def metric_card(label: str, value: Any, help_text: Optional[str] = None) -> None:
    st.metric(label=label, value=value, help=help_text)


def format_score(value: Any) -> str:
    try:
        if pd.isna(value):
            return "-"
        return f"{float(value):.2f}"
    except Exception:
        return "-"


def display_summary_cards(df: pd.DataFrame) -> None:
    if df.empty:
        st.warning("No rows found for the selected theme/date.")
        return

    total_rows = len(df)

    avg_theme_score = df["theme_score"].mean() if "theme_score" in df.columns else None
    max_theme_score = df["theme_score"].max() if "theme_score" in df.columns else None
    avg_confidence = df["confidence_score"].mean() if "confidence_score" in df.columns else None
    avg_evidence = df["evidence_count"].mean() if "evidence_count" in df.columns else None

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        metric_card("Rows", total_rows)

    with c2:
        metric_card("Avg Theme Score", format_score(avg_theme_score))

    with c3:
        metric_card("Highest Score", format_score(max_theme_score))

    with c4:
        metric_card("Avg Confidence", format_score(avg_confidence))

    with c5:
        metric_card("Avg Evidence Count", format_score(avg_evidence))


def display_top_table(df: pd.DataFrame) -> None:
    if df.empty:
        return

    display_cols = [
        "run_date_sgt",
        "theme_name",
        "theme_version",
        "ticker",
        "company",
        "sector",
        "subsector",
        "theme_score",
        "confidence_score",
        "interaction_score",
        "evidence_count",
        "positive_driver_count",
        "negative_driver_count",
    ]

    existing_cols = [c for c in display_cols if c in df.columns]

    show_df = df[existing_cols].copy()

    if "theme_score" in show_df.columns:
        show_df = show_df.sort_values("theme_score", ascending=False)

    st.dataframe(
        show_df,
        use_container_width=True,
        hide_index=True,
    )


def display_sector_summary(df: pd.DataFrame) -> None:
    if df.empty or "sector" not in df.columns:
        return

    sector_df = (
        df.groupby("sector", dropna=False)
        .agg(
            rows=("ticker", "count"),
            avg_theme_score=("theme_score", "mean"),
            max_theme_score=("theme_score", "max"),
            avg_confidence_score=("confidence_score", "mean"),
        )
        .reset_index()
        .sort_values("avg_theme_score", ascending=False)
    )

    st.dataframe(
        sector_df,
        use_container_width=True,
        hide_index=True,
    )


def display_subsector_summary(df: pd.DataFrame) -> None:
    if df.empty or "subsector" not in df.columns:
        return

    subsector_df = (
        df.groupby(["sector", "subsector"], dropna=False)
        .agg(
            rows=("ticker", "count"),
            avg_theme_score=("theme_score", "mean"),
            max_theme_score=("theme_score", "max"),
            avg_confidence_score=("confidence_score", "mean"),
        )
        .reset_index()
        .sort_values("avg_theme_score", ascending=False)
    )

    st.dataframe(
        subsector_df,
        use_container_width=True,
        hide_index=True,
    )


def display_theme_summary_table(theme_summary: pd.DataFrame) -> None:
    if theme_summary.empty:
        st.info("No structural theme rows found yet.")
        return

    st.dataframe(
        theme_summary,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# MAIN APP
# ============================================================

def main() -> None:
    st.title("📡 Structural Theme Transmission Dashboard")

    st.caption(
        "Generic theme-aware dashboard powered by structural_theme_scores. "
        "AI is currently the first installed theme."
    )

    theme_summary = load_available_theme_summary()

    active_themes = sorted(theme_summary["theme_name"].unique().tolist()) if not theme_summary.empty else ["ai"]

    default_index = 0
    if DEFAULT_THEME in active_themes:
        default_index = active_themes.index(DEFAULT_THEME)

    with st.sidebar:
        st.header("Controls")

        selected_theme = st.selectbox(
            "Theme",
            active_themes,
            index=default_index,
        )

        load_limit = st.number_input(
            "Max rows to load",
            min_value=20,
            max_value=5000,
            value=1000,
            step=100,
        )

        show_all_dates = st.checkbox(
            "Show all dates",
            value=False,
        )

        st.divider()

        st.subheader("Available Themes")
        display_theme_summary_table(theme_summary)

    raw_df = load_theme_scores(
        theme_name=selected_theme,
        run_date_sgt=None,
        limit=int(load_limit),
    )

    if raw_df.empty:
        st.warning(f"No rows returned for theme_name = '{selected_theme}'.")
        st.stop()

    latest_date = get_latest_run_date(raw_df)

    if show_all_dates:
        df = raw_df.copy()
        selected_date = "All dates"
    else:
        selected_date = latest_date
        df = raw_df[raw_df["run_date_sgt"] == latest_date].copy()

    st.subheader(f"Theme: `{selected_theme}`")
    st.caption(f"Selected date: {selected_date}")

    display_summary_cards(df)

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Top Scores",
            "Sector Summary",
            "Subsector Summary",
            "Raw Data",
        ]
    )

    with tab1:
        st.subheader("Top Theme Scores")
        display_top_table(df)

    with tab2:
        st.subheader("Sector Summary")
        display_sector_summary(df)

    with tab3:
        st.subheader("Subsector Summary")
        display_subsector_summary(df)

    with tab4:
        st.subheader("Raw Data")
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.caption(
        "Phase 1 status: Streamlit now reads from the generic structural_theme_scores table "
        "using theme_name filtering."
    )


if __name__ == "__main__":
    main()
