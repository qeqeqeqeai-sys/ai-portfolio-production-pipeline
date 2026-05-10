#!/usr/bin/env python3
"""
ai_transmission_streamlit_app_v1.py

Streamlit dashboard for the AI Transmission feature.

Purpose
-------
Reads public.ai_transmission_scores and public.structural_theme_scores from Supabase REST API and displays:

1. Latest run overview
2. Top AI transmission beneficiaries
3. Top disruption losers
4. Transmission heatmap
5. Sector ranking
6. Score component breakdown
7. Latest scoring table
8. Generic structural theme validation layer

Recommended Streamlit secrets
-----------------------------

In Streamlit Cloud, add these under App settings -> Secrets:

SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_ANON_KEY = "your-anon-key"

Important
---------
Do NOT use SUPABASE_SERVICE_ROLE_KEY in Streamlit frontend apps.
Use SUPABASE_ANON_KEY or a read-only key/role.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import requests
import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI Transmission Monitor",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CONFIG HELPERS
# ============================================================

def get_secret(name: str, default: str = "") -> str:
    """
    Read secrets from Streamlit Cloud first, then environment variables.
    """
    try:
        value = st.secrets.get(name, default)
        if value:
            return str(value)
    except Exception:
        pass

    return os.getenv(name, default)


SUPABASE_URL = get_secret("SUPABASE_URL").rstrip("/")
SUPABASE_ANON_KEY = get_secret("SUPABASE_ANON_KEY")

SCORES_TABLE = "ai_transmission_scores"
STRUCTURAL_SCORES_TABLE = "structural_theme_scores"
DEFAULT_THEME = get_secret("DEFAULT_THEME", "ai")


# ============================================================
# STYLING
# ============================================================

CUSTOM_CSS = """
<style>
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}

.metric-card {
    border-radius: 18px;
    padding: 18px;
    border: 1px solid rgba(128, 128, 128, 0.25);
    background: rgba(250, 250, 250, 0.04);
}

.small-caption {
    font-size: 0.85rem;
    color: #777;
}

.section-title {
    margin-top: 0.5rem;
    margin-bottom: 0.25rem;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ============================================================
# SUPABASE REST
# ============================================================

def supabase_headers() -> Dict[str, str]:
    return {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
    }


@st.cache_data(ttl=300, show_spinner=False)
def fetch_scores(limit: int = 5000) -> pd.DataFrame:
    """
    Fetch transmission scores from Supabase REST API.
    """
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return pd.DataFrame()

    url = f"{SUPABASE_URL}/rest/v1/{SCORES_TABLE}"

    params = {
        "select": "*",
        "order": "run_date_sgt.desc,rank_overall.asc",
        "limit": str(limit),
    }

    response = requests.get(
        url,
        headers=supabase_headers(),
        params=params,
        timeout=30,
    )

    if response.status_code >= 400:
        raise RuntimeError(
            f"Supabase fetch failed: HTTP {response.status_code} - {response.text}"
        )

    data = response.json()

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    # Normalize dates and numeric columns
    if "run_date_sgt" in df.columns:
        df["run_date_sgt"] = pd.to_datetime(df["run_date_sgt"], errors="coerce").dt.date

    numeric_cols = [
        "exposure_score",
        "evidence_score",
        "sentiment_score",
        "market_confirmation_score",
        "confidence_score",
        "transmission_score",
        "rank_overall",
        "rank_sector",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df




@st.cache_data(ttl=300, show_spinner=False)
def fetch_structural_theme_scores(
    theme_name: str = "ai",
    limit: int = 5000,
) -> pd.DataFrame:
    """
    Fetch generic theme-level scores from structural_theme_scores.

    This is the Phase 1 modular architecture table.
    AI is the first installed theme, but future themes should use the same table.
    """
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return pd.DataFrame()

    url = f"{SUPABASE_URL}/rest/v1/{STRUCTURAL_SCORES_TABLE}"

    params = {
        "select": "*",
        "theme_name": f"eq.{theme_name}",
        "order": "run_date_sgt.desc,theme_score.desc",
        "limit": str(limit),
    }

    response = requests.get(
        url,
        headers=supabase_headers(),
        params=params,
        timeout=30,
    )

    if response.status_code >= 400:
        raise RuntimeError(
            f"Supabase structural theme fetch failed: HTTP {response.status_code} - {response.text}"
        )

    data = response.json()

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    if "run_date_sgt" in df.columns:
        df["run_date_sgt"] = pd.to_datetime(df["run_date_sgt"], errors="coerce").dt.date

    if "run_timestamp_sgt" in df.columns:
        df["run_timestamp_sgt"] = pd.to_datetime(df["run_timestamp_sgt"], errors="coerce")

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


@st.cache_data(ttl=300, show_spinner=False)
def fetch_structural_theme_catalog(limit: int = 5000) -> pd.DataFrame:
    """
    Fetch a lightweight catalog of available themes.
    """
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return pd.DataFrame()

    url = f"{SUPABASE_URL}/rest/v1/{STRUCTURAL_SCORES_TABLE}"

    params = {
        "select": "theme_name,theme_version,run_date_sgt,ticker,theme_score,confidence_score",
        "order": "theme_name.asc,run_date_sgt.desc",
        "limit": str(limit),
    }

    response = requests.get(
        url,
        headers=supabase_headers(),
        params=params,
        timeout=30,
    )

    if response.status_code >= 400:
        raise RuntimeError(
            f"Supabase structural theme catalog fetch failed: HTTP {response.status_code} - {response.text}"
        )

    data = response.json()

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    if "run_date_sgt" in df.columns:
        df["run_date_sgt"] = pd.to_datetime(df["run_date_sgt"], errors="coerce").dt.date

    for col in ["theme_score", "confidence_score"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def summarize_theme_catalog(theme_catalog: pd.DataFrame) -> pd.DataFrame:
    if theme_catalog.empty or "theme_name" not in theme_catalog.columns:
        return pd.DataFrame()

    summary = (
        theme_catalog.groupby("theme_name", as_index=False)
        .agg(
            rows=("ticker", "count"),
            latest_run_date=("run_date_sgt", "max"),
            avg_theme_score=("theme_score", "mean"),
            avg_confidence_score=("confidence_score", "mean"),
        )
        .sort_values("theme_name")
    )

    for col in ["avg_theme_score", "avg_confidence_score"]:
        if col in summary.columns:
            summary[col] = summary[col].round(2)

    return summary

# ============================================================
# DATA HELPERS
# ============================================================

def latest_run_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "run_date_sgt" not in df.columns:
        return pd.DataFrame()

    latest_date = df["run_date_sgt"].max()
    return df[df["run_date_sgt"] == latest_date].copy()


def safe_mean(series: pd.Series) -> float:
    value = pd.to_numeric(series, errors="coerce").mean()
    if pd.isna(value):
        return 0.0
    return float(value)


def format_score(value: Any) -> str:
    try:
        if pd.isna(value):
            return "-"
        return f"{float(value):.1f}"
    except Exception:
        return "-"


def direction_label(direction: str) -> str:
    if direction == "POSITIVE":
        return "Beneficiary"
    if direction == "NEGATIVE":
        return "Disruption Loser"
    if direction == "MIXED":
        return "Mixed"
    return "Uncertain"


def build_heatmap(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    needed = {"ai_subsector", "affected_sector", "transmission_score"}
    if not needed.issubset(df.columns):
        return pd.DataFrame()

    heatmap = (
        df.groupby(["ai_subsector", "affected_sector"], as_index=False)
        .agg(avg_transmission_score=("transmission_score", "mean"))
    )

    pivot = heatmap.pivot(
        index="ai_subsector",
        columns="affected_sector",
        values="avg_transmission_score",
    )

    return pivot




def display_structural_theme_overview(
    structural_df: pd.DataFrame,
    *,
    selected_theme: str,
    show_all_dates: bool,
) -> pd.DataFrame:
    """
    Display the new generic structural-theme layer while preserving the legacy AI dashboard below.
    Returns the date-filtered structural dataframe for downstream use.
    """
    st.markdown("## Generic Structural Theme Layer")
    st.caption(
        "Phase 1 validation layer. This section reads from `structural_theme_scores` "
        "using `theme_name` filtering. The legacy AI transmission dashboard remains below."
    )

    if structural_df.empty:
        st.warning(f"No rows found in structural_theme_scores for theme_name = '{selected_theme}'.")
        return pd.DataFrame()

    latest_structural_date = structural_df["run_date_sgt"].max() if "run_date_sgt" in structural_df.columns else None

    if show_all_dates or latest_structural_date is None:
        view_df = structural_df.copy()
        selected_date_label = "All dates"
    else:
        view_df = structural_df[structural_df["run_date_sgt"] == latest_structural_date].copy()
        selected_date_label = str(latest_structural_date)

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.metric("Theme", selected_theme)
    with c2:
        st.metric("Run Date", selected_date_label)
    with c3:
        st.metric("Rows", f"{len(view_df):,}")
    with c4:
        avg_theme_score = safe_mean(view_df["theme_score"]) if "theme_score" in view_df.columns else 0.0
        st.metric("Avg Theme Score", format_score(avg_theme_score))
    with c5:
        avg_confidence = safe_mean(view_df["confidence_score"]) if "confidence_score" in view_df.columns else 0.0
        st.metric("Avg Confidence", format_score(avg_confidence))

    tab_theme_top, tab_theme_sector, tab_theme_raw = st.tabs(
        ["Top Theme Scores", "Theme Sector Summary", "Theme Raw Data"]
    )

    with tab_theme_top:
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
        display_cols = [c for c in display_cols if c in view_df.columns]

        if display_cols:
            sort_col = "theme_score" if "theme_score" in view_df.columns else display_cols[0]
            st.dataframe(
                view_df.sort_values(sort_col, ascending=False)[display_cols],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No displayable structural theme columns found.")

    with tab_theme_sector:
        if view_df.empty or "sector" not in view_df.columns:
            st.info("No sector data available in structural theme layer.")
        else:
            sector_theme = (
                view_df.groupby("sector", dropna=False, as_index=False)
                .agg(
                    rows=("ticker", "count"),
                    avg_theme_score=("theme_score", "mean"),
                    max_theme_score=("theme_score", "max"),
                    avg_confidence_score=("confidence_score", "mean"),
                )
                .sort_values("avg_theme_score", ascending=False)
            )

            for col in ["avg_theme_score", "max_theme_score", "avg_confidence_score"]:
                if col in sector_theme.columns:
                    sector_theme[col] = sector_theme[col].round(2)

            st.dataframe(
                sector_theme,
                use_container_width=True,
                hide_index=True,
            )

    with tab_theme_raw:
        st.dataframe(
            view_df,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()
    return view_df

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🧠 AI Transmission")

st.sidebar.caption(
    "Structural AI impact monitor across sectors, subsectors and stocks."
)

refresh = st.sidebar.button("Refresh data", use_container_width=True)
if refresh:
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()

st.sidebar.subheader("Filters")

st.sidebar.markdown("### Generic Theme Layer")

# These controls validate the new generic structural_theme_scores architecture.
try:
    theme_catalog_sidebar = fetch_structural_theme_catalog()
    theme_summary_sidebar = summarize_theme_catalog(theme_catalog_sidebar)
except Exception:
    theme_catalog_sidebar = pd.DataFrame()
    theme_summary_sidebar = pd.DataFrame()

if not theme_summary_sidebar.empty and "theme_name" in theme_summary_sidebar.columns:
    available_themes = sorted(theme_summary_sidebar["theme_name"].dropna().unique().tolist())
else:
    available_themes = [DEFAULT_THEME or "ai"]

default_theme_index = 0
if DEFAULT_THEME in available_themes:
    default_theme_index = available_themes.index(DEFAULT_THEME)

selected_theme = st.sidebar.selectbox(
    "Theme name",
    options=available_themes,
    index=default_theme_index,
)

show_all_theme_dates = st.sidebar.checkbox(
    "Show all theme dates",
    value=False,
)

if not theme_summary_sidebar.empty:
    with st.sidebar.expander("Available theme summary", expanded=False):
        st.dataframe(
            theme_summary_sidebar,
            use_container_width=True,
            hide_index=True,
        )

st.sidebar.divider()

st.sidebar.markdown("### Legacy AI Transmission Layer")

# ============================================================
# MAIN APP
# ============================================================

st.title("AI Transmission Monitor v1")
st.caption(
    "Tracks how AI infrastructure, software and semiconductor themes transmit into non-AI sectors and stocks."
)

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    st.error(
        "Missing Supabase credentials. Add SUPABASE_URL and SUPABASE_ANON_KEY "
        "to Streamlit secrets or environment variables."
    )
    st.stop()

try:
    structural_scores = fetch_structural_theme_scores(
        theme_name=selected_theme,
        limit=5000,
    )
except Exception as exc:
    st.error(f"Unable to load structural theme scores: {exc}")
    structural_scores = pd.DataFrame()

structural_view_df = display_structural_theme_overview(
    structural_scores,
    selected_theme=selected_theme,
    show_all_dates=show_all_theme_dates,
)

try:
    all_scores = fetch_scores()
except Exception as exc:
    st.error(str(exc))
    st.stop()

if all_scores.empty:
    st.warning("No rows found in ai_transmission_scores yet.")
    st.stop()

latest_df = latest_run_df(all_scores)

if latest_df.empty:
    st.warning("No latest run rows available.")
    st.stop()

latest_date = latest_df["run_date_sgt"].max()

# Sidebar filter options
direction_options = sorted(latest_df["transmission_direction"].dropna().unique().tolist())
sector_options = sorted(latest_df["affected_sector"].dropna().unique().tolist())
regime_options = sorted(latest_df["transmission_regime"].dropna().unique().tolist())

selected_directions = st.sidebar.multiselect(
    "Transmission direction",
    options=direction_options,
    default=direction_options,
)

selected_sectors = st.sidebar.multiselect(
    "Affected sector",
    options=sector_options,
    default=sector_options,
)

selected_regimes = st.sidebar.multiselect(
    "Regime",
    options=regime_options,
    default=regime_options,
)

min_score = st.sidebar.slider(
    "Minimum transmission score",
    min_value=0,
    max_value=100,
    value=0,
    step=5,
)

filtered_df = latest_df.copy()

if selected_directions:
    filtered_df = filtered_df[filtered_df["transmission_direction"].isin(selected_directions)]

if selected_sectors:
    filtered_df = filtered_df[filtered_df["affected_sector"].isin(selected_sectors)]

if selected_regimes:
    filtered_df = filtered_df[filtered_df["transmission_regime"].isin(selected_regimes)]

filtered_df = filtered_df[filtered_df["transmission_score"].fillna(0) >= min_score]


# ============================================================
# OVERVIEW
# ============================================================

st.markdown("## Latest Run Overview")

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

top_row = latest_df.sort_values("transmission_score", ascending=False).head(1)
top_name = "-"
top_score = "-"

if not top_row.empty:
    top_name = str(top_row.iloc[0].get("affected_ticker") or top_row.iloc[0].get("affected_company") or "-")
    top_score = format_score(top_row.iloc[0].get("transmission_score"))

positive_count = int((latest_df["transmission_direction"] == "POSITIVE").sum())
negative_count = int((latest_df["transmission_direction"] == "NEGATIVE").sum())
mixed_count = int((latest_df["transmission_direction"] == "MIXED").sum())

extreme_count = int((latest_df["transmission_regime"] == "EXTREME").sum())
avg_score = safe_mean(latest_df["transmission_score"])

kpi1.metric("Latest Run Date", str(latest_date))
kpi2.metric("Rows Scored", f"{len(latest_df):,}")
kpi3.metric("Average Score", format_score(avg_score))
kpi4.metric("Extreme Regimes", f"{extreme_count:,}")
kpi5.metric("Top Signal", top_name, delta=f"Score {top_score}")

st.caption(
    f"Positive: {positive_count} | Negative: {negative_count} | Mixed: {mixed_count}"
)

st.divider()


# ============================================================
# TOP BENEFICIARIES / LOSERS
# ============================================================

left, right = st.columns(2)

with left:
    st.markdown("### Top AI Transmission Beneficiaries")

    beneficiaries = (
        latest_df[latest_df["transmission_direction"] == "POSITIVE"]
        .sort_values("transmission_score", ascending=False)
        .head(10)
    )

    if beneficiaries.empty:
        st.info("No positive transmission rows found.")
    else:
        display_cols = [
            "rank_overall",
            "affected_ticker",
            "affected_company",
            "affected_sector",
            "affected_subsector",
            "transmission_score",
            "transmission_regime",
            "signal_label",
        ]
        display_cols = [c for c in display_cols if c in beneficiaries.columns]
        st.dataframe(
            beneficiaries[display_cols],
            use_container_width=True,
            hide_index=True,
        )

with right:
    st.markdown("### Top Disruption Losers")

    losers = (
        latest_df[latest_df["transmission_direction"] == "NEGATIVE"]
        .sort_values("transmission_score", ascending=False)
        .head(10)
    )

    if losers.empty:
        st.info("No negative transmission rows found.")
    else:
        display_cols = [
            "rank_overall",
            "affected_ticker",
            "affected_company",
            "affected_sector",
            "affected_subsector",
            "transmission_score",
            "transmission_regime",
            "signal_label",
        ]
        display_cols = [c for c in display_cols if c in losers.columns]
        st.dataframe(
            losers[display_cols],
            use_container_width=True,
            hide_index=True,
        )

st.divider()


# ============================================================
# CHARTS
# ============================================================

st.markdown("## Transmission Analytics")

chart_left, chart_right = st.columns(2)

with chart_left:
    st.markdown("### Top Transmission Scores")

    top_chart = filtered_df.sort_values("transmission_score", ascending=False).head(20)

    if top_chart.empty:
        st.info("No rows match current filters.")
    else:
        top_chart = top_chart.copy()
        top_chart["display_name"] = top_chart.apply(
            lambda r: str(r.get("affected_ticker") or r.get("affected_company") or "Unknown"),
            axis=1,
        )

        fig = px.bar(
            top_chart.sort_values("transmission_score", ascending=True),
            x="transmission_score",
            y="display_name",
            orientation="h",
            color="transmission_direction",
            hover_data=[
                "affected_company",
                "affected_sector",
                "affected_subsector",
                "transmission_regime",
                "signal_label",
            ],
            labels={
                "transmission_score": "Transmission Score",
                "display_name": "Ticker / Company",
                "transmission_direction": "Direction",
            },
            height=550,
        )
        st.plotly_chart(fig, use_container_width=True)

with chart_right:
    st.markdown("### Regime Distribution")

    regime_counts = (
        filtered_df.groupby(["transmission_regime", "transmission_direction"], as_index=False)
        .size()
        .rename(columns={"size": "count"})
    )

    if regime_counts.empty:
        st.info("No regime data available.")
    else:
        fig = px.bar(
            regime_counts,
            x="transmission_regime",
            y="count",
            color="transmission_direction",
            barmode="group",
            labels={
                "transmission_regime": "Regime",
                "count": "Count",
                "transmission_direction": "Direction",
            },
            height=550,
        )
        st.plotly_chart(fig, use_container_width=True)

st.divider()


# ============================================================
# HEATMAP
# ============================================================

st.markdown("## Transmission Heatmap")
st.caption("Average transmission score by AI subsector and affected sector.")

heatmap_df = build_heatmap(filtered_df)

if heatmap_df.empty:
    st.info("Not enough data to build heatmap.")
else:
    fig = px.imshow(
        heatmap_df,
        text_auto=".1f",
        aspect="auto",
        labels=dict(
            x="Affected Sector",
            y="AI Subsector",
            color="Avg Score",
        ),
        height=520,
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()


# ============================================================
# SECTOR RANKING + COMPONENT BREAKDOWN
# ============================================================

sector_col, component_col = st.columns(2)

with sector_col:
    st.markdown("### Sector Transmission Ranking")

    sector_rank = (
        filtered_df.groupby("affected_sector", as_index=False)
        .agg(
            avg_transmission_score=("transmission_score", "mean"),
            max_transmission_score=("transmission_score", "max"),
            rows=("id", "count") if "id" in filtered_df.columns else ("transmission_score", "count"),
        )
        .sort_values("avg_transmission_score", ascending=False)
    )

    if sector_rank.empty:
        st.info("No sector ranking available.")
    else:
        sector_rank["avg_transmission_score"] = sector_rank["avg_transmission_score"].round(2)
        sector_rank["max_transmission_score"] = sector_rank["max_transmission_score"].round(2)

        st.dataframe(
            sector_rank,
            use_container_width=True,
            hide_index=True,
        )

with component_col:
    st.markdown("### Score Component Breakdown")

    component_cols = [
        "exposure_score",
        "evidence_score",
        "sentiment_score",
        "market_confirmation_score",
        "confidence_score",
    ]

    available_components = [c for c in component_cols if c in filtered_df.columns]

    if not available_components or filtered_df.empty:
        st.info("No score component data available.")
    else:
        component_means = (
            filtered_df[available_components]
            .mean(numeric_only=True)
            .reset_index()
        )
        component_means.columns = ["component", "average_score"]
        component_means["average_score"] = component_means["average_score"].round(2)

        fig = px.bar(
            component_means,
            x="component",
            y="average_score",
            labels={
                "component": "Component",
                "average_score": "Average Score",
            },
            height=420,
        )
        st.plotly_chart(fig, use_container_width=True)

st.divider()


# ============================================================
# DETAIL EXPLORER
# ============================================================

st.markdown("## Latest Scoring Table")

table_cols = [
    "rank_overall",
    "rank_sector",
    "run_date_sgt",
    "ai_subsector",
    "affected_sector",
    "affected_subsector",
    "affected_ticker",
    "affected_company",
    "transmission_direction",
    "transmission_type",
    "exposure_score",
    "evidence_score",
    "sentiment_score",
    "market_confirmation_score",
    "confidence_score",
    "transmission_score",
    "transmission_regime",
    "signal_label",
    "source",
]

table_cols = [c for c in table_cols if c in filtered_df.columns]

table_df = filtered_df.sort_values(
    ["rank_overall", "transmission_score"],
    ascending=[True, False],
)[table_cols].copy()

st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True,
)

csv = table_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download latest filtered table as CSV",
    data=csv,
    file_name=f"ai_transmission_scores_{latest_date}.csv",
    mime="text/csv",
    use_container_width=True,
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "v1 dashboard with Phase 1 modular refactor. The legacy AI-specific views remain powered by "
    "ai_transmission_scores, while the new generic validation layer reads structural_theme_scores "
    "using theme_name filtering."
)
