#!/usr/bin/env python3
"""
ai_transmission_streamlit_app_v1.py

Streamlit dashboard for the AI Transmission feature.

Purpose
-------
Reads public.ai_transmission_scores from Supabase REST API and displays:

1. Latest run overview
2. Top AI transmission beneficiaries
3. Top disruption losers
4. Transmission heatmap
5. Sector ranking
6. Score component breakdown
7. Latest scoring table

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

# ============================================================
# MAIN APP
# ============================================================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_ANON_KEY"]

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}

url = (
    f"{SUPABASE_URL}/rest/v1/structural_theme_scores"
    "?select=*"
    "&theme_name=eq.ai"
    "&order=theme_score.desc"
    "&limit=20"
)

response = requests.get(url, headers=headers)

st.write("HTTP Status:", response.status_code)

if response.status_code == 200:
    data = response.json()

    st.write("Rows returned:", len(data))

    df = pd.DataFrame(data)

    st.dataframe(df)

else:
    st.error(response.text)

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
    "v1 dashboard. Evidence and sentiment scores are placeholders until the observation layer is connected."
)
