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
For private Streamlit dashboards, SUPABASE_SERVICE_ROLE_KEY can be stored in Streamlit secrets for server-side read access to RLS-protected tables. Otherwise use SUPABASE_ANON_KEY with explicit SELECT RLS policies.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, date
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
# Optional server-side read key for private/RLS-protected historical tables.
# In Streamlit Cloud this remains server-side in st.secrets.
SUPABASE_SERVICE_ROLE_KEY = get_secret("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_READ_KEY = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY

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
    """
    Supabase REST headers.

    Phase 2D historical tables may be protected by RLS even when older
    dashboard tables are readable with the anon key. If a
    SUPABASE_SERVICE_ROLE_KEY is supplied in Streamlit secrets, this app uses
    it server-side for read access. Otherwise it falls back to anon.
    """
    key = SUPABASE_READ_KEY
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Prefer": "count=exact",
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


# ============================================================
# PHASE 2C EXPLAINABILITY HELPERS
# ============================================================

EXPLANATIONS_TABLE = "structural_theme_explanations"
COMPONENT_SCORES_TABLE = "structural_theme_component_scores"
EVIDENCE_ATTRIBUTION_TABLE = "structural_theme_evidence_attribution"


def normalize_json_cell(value: Any) -> Any:
    """Safely normalize Supabase jsonb values returned as dict/list/string."""
    if value is None:
        return None
    if isinstance(value, (list, dict)):
        return value
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            import json
            return json.loads(value)
        except Exception:
            return value
    return value


def json_list_to_df(value: Any) -> pd.DataFrame:
    data = normalize_json_cell(value)
    if data is None:
        return pd.DataFrame()
    if isinstance(data, dict):
        # Common pattern: {"items": [...]} or {"drivers": [...]}
        for key in ["items", "drivers", "pathways", "components", "data"]:
            if isinstance(data.get(key), list):
                data = data[key]
                break
        else:
            data = [data]
    if not isinstance(data, list):
        return pd.DataFrame({"value": [str(data)]})
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


def normalize_ticker_column(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    if "ticker" not in out.columns:
        for candidate in ["affected_ticker", "symbol"]:
            if candidate in out.columns:
                out["ticker"] = out[candidate]
                break
    return out


@st.cache_data(ttl=300, show_spinner=False)
def fetch_phase2b_explanations(theme_name: str = "ai", limit: int = 5000) -> pd.DataFrame:
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return pd.DataFrame()

    url = f"{SUPABASE_URL}/rest/v1/{EXPLANATIONS_TABLE}"
    params = {
        "select": "*",
        "theme_name": f"eq.{theme_name}",
        "order": "run_date_sgt.desc,final_score.desc",
        "limit": str(limit),
    }

    response = requests.get(url, headers=supabase_headers(), params=params, timeout=30)

    if response.status_code >= 400:
        # Do not break the main dashboard if Phase 2B tables are not readable yet.
        return pd.DataFrame()

    data = response.json()
    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    if "run_date_sgt" in df.columns:
        df["run_date_sgt"] = pd.to_datetime(df["run_date_sgt"], errors="coerce").dt.date
    if "run_timestamp_sgt" in df.columns:
        df["run_timestamp_sgt"] = pd.to_datetime(df["run_timestamp_sgt"], errors="coerce")

    for col in ["final_score", "confidence_score", "evidence_count", "relationship_count"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return normalize_ticker_column(df)


@st.cache_data(ttl=300, show_spinner=False)
def fetch_phase2b_component_scores(theme_name: str = "ai", limit: int = 10000) -> pd.DataFrame:
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return pd.DataFrame()

    url = f"{SUPABASE_URL}/rest/v1/{COMPONENT_SCORES_TABLE}"
    params = {
        "select": "*",
        "theme_name": f"eq.{theme_name}",
        "order": "run_date_sgt.desc,ticker.asc,component_rank.asc",
        "limit": str(limit),
    }

    response = requests.get(url, headers=supabase_headers(), params=params, timeout=30)

    if response.status_code >= 400:
        return pd.DataFrame()

    data = response.json()
    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    if "run_date_sgt" in df.columns:
        df["run_date_sgt"] = pd.to_datetime(df["run_date_sgt"], errors="coerce").dt.date
    if "run_timestamp_sgt" in df.columns:
        df["run_timestamp_sgt"] = pd.to_datetime(df["run_timestamp_sgt"], errors="coerce")

    for col in ["component_score", "component_weight", "weighted_contribution", "contribution_pct", "component_rank"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return normalize_ticker_column(df)


@st.cache_data(ttl=300, show_spinner=False)
def fetch_phase2b_evidence_attribution(theme_name: str = "ai", limit: int = 10000) -> pd.DataFrame:
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return pd.DataFrame()

    url = f"{SUPABASE_URL}/rest/v1/{EVIDENCE_ATTRIBUTION_TABLE}"
    params = {
        "select": "*",
        "theme_name": f"eq.{theme_name}",
        "order": "run_date_sgt.desc,contribution_score.desc",
        "limit": str(limit),
    }

    response = requests.get(url, headers=supabase_headers(), params=params, timeout=30)

    if response.status_code >= 400:
        return pd.DataFrame()

    data = response.json()
    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    if "run_date_sgt" in df.columns:
        df["run_date_sgt"] = pd.to_datetime(df["run_date_sgt"], errors="coerce").dt.date
    if "run_timestamp_sgt" in df.columns:
        df["run_timestamp_sgt"] = pd.to_datetime(df["run_timestamp_sgt"], errors="coerce")

    numeric_cols = [
        "ai_relevance_score",
        "impact_magnitude_score",
        "sentiment_score",
        "confidence_score",
        "direction_adjusted_sentiment_score",
        "evidence_quality_score",
        "evidence_weight",
        "contribution_score",
        "signed_contribution_score",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return normalize_ticker_column(df)


def latest_by_date(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "run_date_sgt" not in df.columns:
        return pd.DataFrame()
    latest_date = df["run_date_sgt"].max()
    return df[df["run_date_sgt"] == latest_date].copy()


def compact_json_table(value: Any, max_rows: int = 8) -> pd.DataFrame:
    df = json_list_to_df(value)
    if df.empty:
        return df
    # Prefer institutionally useful columns when available.
    preferred = [
        "driver",
        "driver_category",
        "category",
        "pathway",
        "transmission_direction",
        "impact_score",
        "contribution_score",
        "signed_contribution_score",
        "evidence_count",
        "weight",
        "score",
        "summary",
    ]
    cols = [c for c in preferred if c in df.columns] + [c for c in df.columns if c not in preferred]
    return df[cols].head(max_rows)


def display_explainability_layer(
    explanations_df: pd.DataFrame,
    components_df: pd.DataFrame,
    evidence_attr_df: pd.DataFrame,
    *,
    selected_theme: str,
    show_all_dates: bool,
) -> None:
    """Render Phase 2C visualization layer using Phase 2B explainability tables."""
    st.markdown("## Phase 2C Explainability Layer")
    st.caption(
        "Visualizes Phase 2B outputs: top drivers, component decomposition, evidence attribution, "
        "contribution weights and transmission pathway traceability."
    )

    if explanations_df.empty and components_df.empty and evidence_attr_df.empty:
        st.warning(
            "No Phase 2B explainability rows found yet, or Streamlit read access is blocked by RLS. "
            "Expected tables: structural_theme_explanations, structural_theme_component_scores, "
            "structural_theme_evidence_attribution."
        )
        st.divider()
        return

    explanations_view = explanations_df.copy()
    components_view = components_df.copy()
    evidence_view = evidence_attr_df.copy()

    latest_dates = []
    for df in [explanations_view, components_view, evidence_view]:
        if not df.empty and "run_date_sgt" in df.columns:
            latest_dates.append(df["run_date_sgt"].max())

    latest_explainability_date = max(latest_dates) if latest_dates else None

    if not show_all_dates and latest_explainability_date is not None:
        if not explanations_view.empty and "run_date_sgt" in explanations_view.columns:
            explanations_view = explanations_view[explanations_view["run_date_sgt"] == latest_explainability_date].copy()
        if not components_view.empty and "run_date_sgt" in components_view.columns:
            components_view = components_view[components_view["run_date_sgt"] == latest_explainability_date].copy()
        if not evidence_view.empty and "run_date_sgt" in evidence_view.columns:
            evidence_view = evidence_view[evidence_view["run_date_sgt"] == latest_explainability_date].copy()

    ticker_options = []
    for df in [explanations_view, components_view, evidence_view]:
        if not df.empty and "ticker" in df.columns:
            ticker_options.extend(df["ticker"].dropna().astype(str).unique().tolist())
    ticker_options = sorted(set(ticker_options))

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Theme", selected_theme)
    with c2:
        st.metric("Explainability Date", str(latest_explainability_date) if latest_explainability_date else "All")
    with c3:
        st.metric("Explanations", f"{len(explanations_view):,}")
    with c4:
        st.metric("Component Rows", f"{len(components_view):,}")
    with c5:
        st.metric("Evidence Attribution Rows", f"{len(evidence_view):,}")

    if not ticker_options:
        st.info("No ticker-level explainability available yet.")
        st.divider()
        return

    default_ticker = ticker_options[0]
    if not explanations_view.empty and "final_score" in explanations_view.columns and "ticker" in explanations_view.columns:
        ranked = explanations_view.sort_values("final_score", ascending=False)
        if not ranked.empty:
            default_ticker = str(ranked.iloc[0]["ticker"])

    selected_ticker = st.selectbox(
        "Select ticker for explainability drilldown",
        options=ticker_options,
        index=ticker_options.index(default_ticker) if default_ticker in ticker_options else 0,
        key="phase2c_selected_ticker",
    )

    ticker_explanation = explanations_view[
        explanations_view.get("ticker", pd.Series(dtype=str)).astype(str) == selected_ticker
    ].copy() if not explanations_view.empty and "ticker" in explanations_view.columns else pd.DataFrame()

    ticker_components = components_view[
        components_view.get("ticker", pd.Series(dtype=str)).astype(str) == selected_ticker
    ].copy() if not components_view.empty and "ticker" in components_view.columns else pd.DataFrame()

    ticker_evidence = evidence_view[
        evidence_view.get("ticker", pd.Series(dtype=str)).astype(str) == selected_ticker
    ].copy() if not evidence_view.empty and "ticker" in evidence_view.columns else pd.DataFrame()

    # Summary cards for selected ticker.
    if not ticker_explanation.empty:
        row = ticker_explanation.sort_values("run_timestamp_sgt", ascending=False).iloc[0] if "run_timestamp_sgt" in ticker_explanation.columns else ticker_explanation.iloc[0]
        s1, s2, s3, s4, s5 = st.columns(5)
        with s1:
            st.metric("Ticker", selected_ticker)
        with s2:
            st.metric("Final Score", format_score(row.get("final_score")))
        with s3:
            st.metric("Confidence", format_score(row.get("confidence_score")))
        with s4:
            st.metric("Evidence Count", int(row.get("evidence_count", 0) or 0))
        with s5:
            st.metric("Relationships", int(row.get("relationship_count", 0) or 0))

        if row.get("evidence_summary"):
            st.info(str(row.get("evidence_summary")))

    tab_drivers, tab_components, tab_evidence, tab_pathways, tab_summary = st.tabs(
        [
            "Top Drivers",
            "Component Decomposition",
            "Evidence Attribution",
            "Pathway Traceability",
            "Explainability Summary",
        ]
    )

    with tab_drivers:
        if ticker_explanation.empty:
            st.info("No explanation row found for selected ticker.")
        else:
            row = ticker_explanation.iloc[0]
            left, right = st.columns(2)

            with left:
                st.markdown("### Top Positive Drivers")
                pos_df = compact_json_table(row.get("top_positive_drivers"), max_rows=10)
                if pos_df.empty:
                    st.info("No positive drivers found.")
                else:
                    st.dataframe(pos_df, use_container_width=True, hide_index=True)

            with right:
                st.markdown("### Top Negative Drivers")
                neg_df = compact_json_table(row.get("top_negative_drivers"), max_rows=10)
                if neg_df.empty:
                    st.info("No negative drivers found.")
                else:
                    st.dataframe(neg_df, use_container_width=True, hide_index=True)

    with tab_components:
        if ticker_components.empty:
            # Fallback to JSON decomposition in explanations table.
            if not ticker_explanation.empty:
                row = ticker_explanation.iloc[0]
                fallback = compact_json_table(row.get("component_decomposition"), max_rows=20)
                if fallback.empty:
                    st.info("No component decomposition found for selected ticker.")
                else:
                    st.dataframe(fallback, use_container_width=True, hide_index=True)
            else:
                st.info("No component decomposition found for selected ticker.")
        else:
            comp = ticker_components.copy()
            sort_col = "component_rank" if "component_rank" in comp.columns else "weighted_contribution"
            comp = comp.sort_values(sort_col, ascending=True if sort_col == "component_rank" else False)

            metric_cols = [
                "component_name",
                "component_score",
                "component_weight",
                "weighted_contribution",
                "contribution_pct",
                "component_rank",
            ]
            metric_cols = [c for c in metric_cols if c in comp.columns]

            chart_cols = [c for c in ["component_name", "weighted_contribution", "component_score"] if c in comp.columns]
            if {"component_name", "weighted_contribution"}.issubset(comp.columns):
                fig = px.bar(
                    comp.sort_values("weighted_contribution", ascending=True),
                    x="weighted_contribution",
                    y="component_name",
                    orientation="h",
                    hover_data=[c for c in ["component_score", "component_weight", "contribution_pct"] if c in comp.columns],
                    labels={
                        "weighted_contribution": "Weighted Contribution",
                        "component_name": "Component",
                    },
                    height=420,
                )
                st.plotly_chart(fig, use_container_width=True)

            st.dataframe(comp[metric_cols], use_container_width=True, hide_index=True)

    with tab_evidence:
        if ticker_evidence.empty:
            st.info("No evidence attribution rows found for selected ticker.")
        else:
            evi = ticker_evidence.copy()
            sort_col = "contribution_score" if "contribution_score" in evi.columns else "evidence_weight"
            if sort_col in evi.columns:
                evi = evi.sort_values(sort_col, ascending=False)

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Evidence Rows", f"{len(evi):,}")
            with col2:
                st.metric("Avg Evidence Weight", format_score(safe_mean(evi["evidence_weight"])) if "evidence_weight" in evi.columns else "-")
            with col3:
                st.metric("Avg Quality", format_score(safe_mean(evi["evidence_quality_score"])) if "evidence_quality_score" in evi.columns else "-")
            with col4:
                st.metric("Avg Contribution", format_score(safe_mean(evi["contribution_score"])) if "contribution_score" in evi.columns else "-")

            if {"evidence_title", "contribution_score"}.issubset(evi.columns):
                top_evi = evi.head(15).copy()
                top_evi["evidence_label"] = top_evi["evidence_title"].fillna("Untitled evidence").astype(str).str.slice(0, 70)
                fig = px.bar(
                    top_evi.sort_values("contribution_score", ascending=True),
                    x="contribution_score",
                    y="evidence_label",
                    orientation="h",
                    color="contribution_direction" if "contribution_direction" in top_evi.columns else None,
                    hover_data=[c for c in ["evidence_source", "transmission_direction", "evidence_weight", "evidence_quality_score", "confidence_score"] if c in top_evi.columns],
                    labels={
                        "contribution_score": "Contribution Score",
                        "evidence_label": "Evidence",
                    },
                    height=520,
                )
                st.plotly_chart(fig, use_container_width=True)

            display_cols = [
                "run_date_sgt",
                "ticker",
                "company",
                "ai_subsector",
                "transmission_direction",
                "transmission_type",
                "contribution_direction",
                "evidence_source",
                "evidence_title",
                "evidence_url",
                "evidence_weight",
                "evidence_quality_score",
                "contribution_score",
                "signed_contribution_score",
                "confidence_score",
                "pathway",
                "evidence_summary",
            ]
            display_cols = [c for c in display_cols if c in evi.columns]
            st.dataframe(evi[display_cols].head(100), use_container_width=True, hide_index=True)

    with tab_pathways:
        if ticker_evidence.empty and ticker_explanation.empty:
            st.info("No pathway traceability found for selected ticker.")
        else:
            if not ticker_evidence.empty and "pathway" in ticker_evidence.columns:
                path_df = (
                    ticker_evidence.groupby(["pathway"], dropna=False, as_index=False)
                    .agg(
                        evidence_rows=("ticker", "count"),
                        avg_contribution=("contribution_score", "mean"),
                        avg_weight=("evidence_weight", "mean"),
                        avg_confidence=("confidence_score", "mean"),
                    )
                    .sort_values("avg_contribution", ascending=False)
                )
                for col in ["avg_contribution", "avg_weight", "avg_confidence"]:
                    if col in path_df.columns:
                        path_df[col] = path_df[col].round(2)
                st.dataframe(path_df, use_container_width=True, hide_index=True)

                if not path_df.empty and "avg_contribution" in path_df.columns:
                    fig = px.bar(
                        path_df.sort_values("avg_contribution", ascending=True),
                        x="avg_contribution",
                        y="pathway",
                        orientation="h",
                        labels={"avg_contribution": "Avg Contribution", "pathway": "Transmission Pathway"},
                        height=420,
                    )
                    st.plotly_chart(fig, use_container_width=True)
            elif not ticker_explanation.empty:
                row = ticker_explanation.iloc[0]
                path_json = compact_json_table(row.get("transmission_pathways"), max_rows=20)
                if path_json.empty:
                    st.info("No pathway JSON found.")
                else:
                    st.dataframe(path_json, use_container_width=True, hide_index=True)

    with tab_summary:
        if explanations_view.empty:
            st.info("No explainability summary available.")
        else:
            summary_cols = [
                "run_date_sgt",
                "ticker",
                "company",
                "sector",
                "subsector",
                "final_score",
                "confidence_score",
                "evidence_count",
                "relationship_count",
                "evidence_summary",
                "explainability_version",
            ]
            summary_cols = [c for c in summary_cols if c in explanations_view.columns]
            st.dataframe(
                explanations_view.sort_values("final_score", ascending=False)[summary_cols],
                use_container_width=True,
                hide_index=True,
            )

    st.divider()




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
# PHASE 2D.1 — HISTORICAL ANALYTICS VISUALIZATION LAYER
# Additive-only layer. Preserves existing dashboard and Phase 2C UI.
# ============================================================

PHASE2D_TABLES = {
    "momentum": "structural_theme_momentum_history",
    "driver_persistence": "structural_theme_driver_persistence_history",
    "pathway_trend": "structural_theme_pathway_trend_history",
    "evidence_intensity": "structural_theme_evidence_intensity_history",
    "attribution_trend": "structural_theme_attribution_trend_history",
    "regime": "structural_theme_regime_history",
    "propagation": "structural_theme_propagation_history",
}


def _first_existing_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _normalize_phase2d_dates(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    for col in ["run_date_sgt", "run_date", "as_of_date", "created_at", "updated_at"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    if "run_date_sgt" not in df.columns:
        fallback = _first_existing_col(df, ["run_date", "as_of_date", "created_at"])
        if fallback:
            df["run_date_sgt"] = df[fallback]
    return df


def _coerce_numeric_cols(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _plotly_layout(fig, title: str, yaxis_title: Optional[str] = None, height: int = 420):
    fig.update_layout(
        title=title,
        template="plotly_white",
        height=height,
        margin=dict(l=20, r=20, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="left", x=0),
    )
    if yaxis_title:
        fig.update_yaxes(title=yaxis_title)
    return fig


def _empty_chart(title: str):
    st.info(f"No historical data available yet for: {title}")


@st.cache_data(ttl=600, show_spinner=False)
def fetch_phase2d_history_table(
    table_name: str,
    theme_name: str = "ai",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 10000,
) -> pd.DataFrame:
    """
    REST-only generic fetcher for Phase 2D historical analytics tables.

    IMPORTANT REVISION:
    This version intentionally avoids REST-side theme/date filters because
    Supabase/PostgREST returns empty results when a filter references a
    column name that differs across Phase 2D tables.

    Strategy:
    1. Fetch rows using only select + limit.
    2. Detect schema locally.
    3. Normalize date column to run_date_sgt.
    4. Apply theme and date filters locally.

    This is safer for evolving institutional schemas and future multi-theme
    modules.
    """
    if not SUPABASE_URL or not SUPABASE_READ_KEY:
        st.warning("Missing SUPABASE_URL or Supabase read key. Add SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY.")
        return pd.DataFrame()

    url = f"{SUPABASE_URL}/rest/v1/{table_name}"

    # Fetch without schema-dependent REST filters.
    params = {
        "select": "*",
        "limit": str(limit),
    }

    try:
        response = requests.get(
            url,
            headers=supabase_headers(),
            params=params,
            timeout=30,
        )
    except Exception as exc:
        st.warning(f"REST request failed for {table_name}: {exc}")
        return pd.DataFrame()

    if response.status_code >= 400:
        st.warning(
            f"REST error loading {table_name}: "
            f"HTTP {response.status_code} - {response.text[:300]}"
        )
        return pd.DataFrame()

    data = response.json()
    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    df = _normalize_phase2d_dates(df)

    # Resolve theme column dynamically. Your current tables use theme_name='ai'.
    theme_col = _first_existing_col(df, ["theme_name", "theme"])
    theme_value = (theme_name or "").strip().lower()

    if theme_col and theme_value:
        df = df[
            df[theme_col]
            .astype(str)
            .str.strip()
            .str.lower()
            == theme_value
        ].copy()

    # Resolve date column dynamically. The current production schema uses run_date_sgt.
    date_col = _first_existing_col(df, ["run_date_sgt", "run_date", "as_of_date", "created_at"])

    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

        # Always expose canonical run_date_sgt to downstream charts.
        if "run_date_sgt" not in df.columns:
            df["run_date_sgt"] = df[date_col]
        else:
            df["run_date_sgt"] = pd.to_datetime(df["run_date_sgt"], errors="coerce")

        # Inclusive local date filters.
        if start_date:
            start_ts = pd.to_datetime(start_date)
            df = df[df["run_date_sgt"] >= start_ts]

        if end_date:
            # End-date inclusive: include the full selected end day.
            end_ts = pd.to_datetime(end_date) + pd.Timedelta(days=1)
            df = df[df["run_date_sgt"] < end_ts]

        df = df.sort_values("run_date_sgt")

    return df.reset_index(drop=True)


@st.cache_data(ttl=300, show_spinner=False)
def debug_phase2d_history_table(table_name: str, limit: int = 5) -> Dict[str, Any]:
    """
    Minimal diagnostic fetch with no theme/date filters.
    Helps distinguish: empty table vs RLS/no policy vs schema mismatch.
    """
    if not SUPABASE_URL or not SUPABASE_READ_KEY:
        return {"status": "missing_credentials", "raw_rows": 0, "columns": []}

    url = f"{SUPABASE_URL}/rest/v1/{table_name}"
    params = {"select": "*", "limit": str(limit)}

    try:
        response = requests.get(url, headers=supabase_headers(), params=params, timeout=30)
    except Exception as exc:
        return {"status": "request_failed", "error": str(exc), "raw_rows": 0, "columns": []}

    result = {
        "status_code": response.status_code,
        "status": "ok" if response.status_code < 400 else "rest_error",
        "raw_rows": 0,
        "columns": [],
        "using_service_role": bool(SUPABASE_SERVICE_ROLE_KEY),
        "response_preview": response.text[:300],
    }

    if response.status_code >= 400:
        return result

    try:
        data = response.json()
    except Exception:
        result["status"] = "invalid_json"
        return result

    result["raw_rows"] = len(data) if isinstance(data, list) else 0
    if isinstance(data, list) and data:
        result["columns"] = list(data[0].keys())
        sample = data[0].copy()
        for key, value in sample.items():
            sample[key] = str(value)[:80]
        result["sample_row"] = sample

    return result

def load_phase2d_history_bundle(
    theme_name: str,
    start_date_value: date,
    end_date_value: date,
    limit: int = 10000,
) -> Dict[str, pd.DataFrame]:
    start = start_date_value.isoformat() if start_date_value else None
    end = end_date_value.isoformat() if end_date_value else None
    return {
        key: fetch_phase2d_history_table(table, theme_name, start, end, limit)
        for key, table in PHASE2D_TABLES.items()
    }


def plot_phase2d_line(
    df: pd.DataFrame,
    title: str,
    value_candidates: List[str],
    group_candidates: Optional[List[str]] = None,
    zero_line: bool = False,
):
    if df.empty or "run_date_sgt" not in df.columns:
        _empty_chart(title)
        return
    value_col = _first_existing_col(df, value_candidates)
    if not value_col:
        _empty_chart(title)
        return
    group_col = _first_existing_col(df, group_candidates or [])
    df = _coerce_numeric_cols(df, [value_col]).dropna(subset=["run_date_sgt", value_col])
    if df.empty:
        _empty_chart(title)
        return
    fig = px.line(
        df,
        x="run_date_sgt",
        y=value_col,
        color=group_col if group_col else None,
        markers=True,
        hover_data=[c for c in df.columns if c != "run_date_sgt"][:12],
    )
    if zero_line:
        fig.add_hline(y=0, line_dash="dash")
    st.plotly_chart(_plotly_layout(fig, title, value_col), use_container_width=True)


def plot_phase2d_bar_latest(
    df: pd.DataFrame,
    title: str,
    value_candidates: List[str],
    label_candidates: List[str],
    top_n: int = 20,
):
    if df.empty:
        _empty_chart(title)
        return
    value_col = _first_existing_col(df, value_candidates)
    label_col = _first_existing_col(df, label_candidates)
    if not value_col or not label_col:
        _empty_chart(title)
        return
    df = _coerce_numeric_cols(df, [value_col])
    if "run_date_sgt" in df.columns:
        latest = df["run_date_sgt"].max()
        df = df[df["run_date_sgt"] == latest].copy()
    df = df[[label_col, value_col]].dropna().sort_values(value_col, ascending=False).head(top_n)
    if df.empty:
        _empty_chart(title)
        return
    fig = px.bar(df.sort_values(value_col), x=value_col, y=label_col, orientation="h")
    st.plotly_chart(_plotly_layout(fig, title, value_col), use_container_width=True)


def plot_phase2d_heatmap(
    df: pd.DataFrame,
    title: str,
    value_candidates: List[str],
    label_candidates: List[str],
):
    if df.empty or "run_date_sgt" not in df.columns:
        _empty_chart(title)
        return
    value_col = _first_existing_col(df, value_candidates)
    label_col = _first_existing_col(df, label_candidates)
    if not value_col or not label_col:
        _empty_chart(title)
        return
    df = _coerce_numeric_cols(df, [value_col]).dropna(subset=["run_date_sgt", label_col, value_col])
    if df.empty:
        _empty_chart(title)
        return
    pivot = df.pivot_table(index=label_col, columns="run_date_sgt", values=value_col, aggfunc="mean").fillna(0)
    if pivot.empty:
        _empty_chart(title)
        return
    fig = px.imshow(pivot, aspect="auto", labels=dict(x="Run Date", y=label_col, color=value_col))
    st.plotly_chart(_plotly_layout(fig, title, value_col, height=520), use_container_width=True)


def plot_phase2d_area(
    df: pd.DataFrame,
    title: str,
    value_candidates: List[str],
    component_candidates: List[str],
):
    if df.empty or "run_date_sgt" not in df.columns:
        _empty_chart(title)
        return
    value_col = _first_existing_col(df, value_candidates)
    component_col = _first_existing_col(df, component_candidates)
    if not value_col or not component_col:
        _empty_chart(title)
        return
    df = _coerce_numeric_cols(df, [value_col]).dropna(subset=["run_date_sgt", component_col, value_col])
    if df.empty:
        _empty_chart(title)
        return
    grouped = df.groupby(["run_date_sgt", component_col], as_index=False)[value_col].mean()
    fig = px.area(grouped, x="run_date_sgt", y=value_col, color=component_col)
    st.plotly_chart(_plotly_layout(fig, title, value_col), use_container_width=True)


def plot_phase2d_regime_timeline(df: pd.DataFrame):
    title = "Regime Transition Timeline"
    if df.empty or "run_date_sgt" not in df.columns:
        _empty_chart(title)
        return
    regime_col = _first_existing_col(df, ["momentum_regime", "regime", "structural_regime", "propagation_regime", "state", "regime_label"])
    entity_col = _first_existing_col(df, ["entity", "ticker", "asset", "sector", "subsector", "pathway_name", "pathway"])
    if not regime_col:
        _empty_chart(title)
        return
    plot_df = df.copy()
    if not entity_col:
        plot_df["theme"] = plot_df.get("theme_name", "theme")
        entity_col = "theme"
    fig = px.scatter(
        plot_df,
        x="run_date_sgt",
        y=entity_col,
        color=regime_col,
        hover_data=[c for c in plot_df.columns if c != "run_date_sgt"][:12],
    )
    st.plotly_chart(_plotly_layout(fig, title, "Entity / Pathway", height=500), use_container_width=True)


def plot_phase2d_regime_duration(df: pd.DataFrame):
    title = "Regime Duration / Frequency"
    if df.empty:
        _empty_chart(title)
        return
    regime_col = _first_existing_col(df, ["momentum_regime", "regime", "structural_regime", "propagation_regime", "state", "regime_label"])
    duration_col = _first_existing_col(df, ["duration_days", "regime_duration_days", "days_in_regime"])
    if not regime_col:
        _empty_chart(title)
        return
    if duration_col:
        plot_df = _coerce_numeric_cols(df, [duration_col]).groupby(regime_col, as_index=False)[duration_col].mean()
        y_col = duration_col
    else:
        plot_df = df.groupby(regime_col, as_index=False).size()
        y_col = "size"
    fig = px.bar(plot_df, x=regime_col, y=y_col)
    st.plotly_chart(_plotly_layout(fig, title, y_col), use_container_width=True)


def plot_phase2d_concentration(df: pd.DataFrame, title: str, value_candidates: List[str], group_candidates: List[str]):
    if df.empty:
        _empty_chart(title)
        return
    value_col = _first_existing_col(df, value_candidates)
    group_col = _first_existing_col(df, group_candidates)
    if not value_col or not group_col:
        _empty_chart(title)
        return
    df = _coerce_numeric_cols(df, [value_col])
    if "run_date_sgt" in df.columns:
        latest = df["run_date_sgt"].max()
        df = df[df["run_date_sgt"] == latest].copy()
    grouped = df.groupby(group_col, as_index=False)[value_col].mean().dropna().sort_values(value_col, ascending=False).head(20)
    if grouped.empty:
        _empty_chart(title)
        return
    fig = px.pie(grouped, names=group_col, values=value_col, hole=0.45)
    st.plotly_chart(_plotly_layout(fig, title, value_col), use_container_width=True)


def render_phase2d1_historical_analytics_layer(selected_theme: str = "ai") -> None:
    """
    Phase 2D.1 historical analytics visualization layer.
    Additive-only and generic-theme compatible.
    """
    st.markdown("## Phase 2D.1 Historical Analytics Visualization Layer")
    st.caption(
        "Historical propagation momentum, acceleration, driver persistence, evidence intensity, "
        "rolling attribution, regime transitions and pathway stability."
    )

    with st.expander("Historical analytics controls", expanded=True):
        c1, c2, c3, c4 = st.columns([1.1, 1, 1, 1])
        with c1:
            hist_theme = st.text_input("Historical theme name", value=selected_theme or DEFAULT_THEME or "ai")
        with c2:
            lookback_days = st.selectbox("Lookback days", [30, 60, 90, 180, 365, 730], index=2)
        with c3:
            end_date_value = st.date_input("Historical end date", value=datetime.now().date())
        with c4:
            row_limit = st.selectbox("REST row limit", [2500, 5000, 10000, 20000], index=2)
        start_date_value = end_date_value - timedelta(days=int(lookback_days))

    with st.spinner("Loading Phase 2D historical analytics tables..."):
        data = load_phase2d_history_bundle(hist_theme, start_date_value, end_date_value, limit=int(row_limit))

    momentum_df = data.get("momentum", pd.DataFrame())
    driver_df = data.get("driver_persistence", pd.DataFrame())
    pathway_df = data.get("pathway_trend", pd.DataFrame())
    evidence_df = data.get("evidence_intensity", pd.DataFrame())
    attribution_df = data.get("attribution_trend", pd.DataFrame())
    regime_df = data.get("regime", pd.DataFrame())
    propagation_df = data.get("propagation", pd.DataFrame())

    st.markdown("### Historical Coverage Summary")
    k1, k2, k3, k4, k5, k6, k7 = st.columns(7)
    k1.metric("Momentum", f"{len(momentum_df):,}")
    k2.metric("Drivers", f"{len(driver_df):,}")
    k3.metric("Pathways", f"{len(pathway_df):,}")
    k4.metric("Evidence", f"{len(evidence_df):,}")
    k5.metric("Attribution", f"{len(attribution_df):,}")
    k6.metric("Regimes", f"{len(regime_df):,}")
    k7.metric("Propagation", f"{len(propagation_df):,}")

    if all(len(frame) == 0 for frame in [momentum_df, driver_df, pathway_df, evidence_df, attribution_df, regime_df, propagation_df]):
        st.warning(
            "Phase 2D REST fetch returned zero rows. This usually means the historical tables are protected by RLS, "
            "or the Streamlit app is using an anon key without SELECT permission on these new tables."
        )
        with st.expander("Phase 2D REST diagnostics", expanded=True):
            diag_rows = []
            for key, table in PHASE2D_TABLES.items():
                diag = debug_phase2d_history_table(table, limit=3)
                diag_rows.append({
                    "dataset": key,
                    "table": table,
                    "status": diag.get("status"),
                    "http_status": diag.get("status_code"),
                    "raw_rows_no_filter": diag.get("raw_rows"),
                    "using_service_role": diag.get("using_service_role"),
                    "columns_detected": ", ".join(diag.get("columns", [])[:12]),
                    "response_preview": diag.get("response_preview", ""),
                })
            st.dataframe(pd.DataFrame(diag_rows), use_container_width=True, hide_index=True)
            st.caption(
                "If raw_rows_no_filter is 0 while SQL Editor shows rows, add SUPABASE_SERVICE_ROLE_KEY to Streamlit secrets "
                "or create SELECT RLS policies for the Phase 2D history tables."
            )

    tabs = st.tabs([
        "Momentum",
        "Driver Persistence",
        "Evidence",
        "Attribution",
        "Regime",
        "Pathway",
        "Propagation Monitor",
        "Raw Data",
    ])

    entity_cols = ["entity", "ticker", "asset", "sector", "subsector", "pathway_name", "pathway"]
    driver_cols = ["driver", "driver_name", "component", "factor_name", "signal_name"]
    pathway_cols = ["pathway_name", "pathway", "transmission_pathway"]
    attribution_cols = ["component", "driver", "driver_name", "factor_name", "attribution_component"]

    with tabs[0]:
        st.subheader("Momentum Analytics")
        a, b = st.columns(2)
        with a:
            plot_phase2d_line(momentum_df, "Rolling Momentum Trend", ["momentum_30d", "momentum_7d", "rolling_momentum", "propagation_momentum", "momentum_score", "structural_momentum_score", "structural_momentum_", "theme_score"], entity_cols)
        with b:
            plot_phase2d_line(momentum_df, "Propagation Acceleration", ["acceleration_score", "momentum_acceleration", "acceleration", "acceleration_", "acceleration_7d", "acceleration_30d"], entity_cols, zero_line=True)
        c, d = st.columns(2)
        with c:
            plot_phase2d_bar_latest(momentum_df, "Entity Momentum Leaderboard", ["structural_momentum_score", "structural_momentum_", "momentum_30d", "momentum_7d", "rolling_momentum", "propagation_momentum", "momentum_score", "theme_score"], entity_cols)
        with d:
            plot_phase2d_line(propagation_df, "Structural Momentum / Propagation Score", ["structural_momentum_score", "structural_momentum_", "propagation_score", "transmission_score", "structural_score", "composite_score", "theme_score"], entity_cols)

    with tabs[1]:
        st.subheader("Driver Persistence Analytics")
        a, b = st.columns(2)
        with a:
            plot_phase2d_bar_latest(driver_df, "Top Persistent Drivers", ["persistence_days", "duration_days", "active_days", "persistence_score"], driver_cols)
        with b:
            plot_phase2d_bar_latest(driver_df, "Persistence Half-Life", ["half_life_days", "estimated_half_life", "decay_half_life", "decay_rate"], driver_cols)
        a, b = st.columns(2)
        with a:
            plot_phase2d_line(driver_df, "Driver Decay Monitoring", ["decay_rate", "persistence_score", "half_life_days"], driver_cols, zero_line=True)
        with b:
            plot_phase2d_heatmap(driver_df, "Persistence Heatmap", ["persistence_score", "persistence_days", "duration_days", "active_days"], driver_cols)

    with tabs[2]:
        st.subheader("Evidence Analytics")
        a, b = st.columns(2)
        with a:
            plot_phase2d_line(evidence_df, "Evidence Intensity Trends", ["evidence_intensity", "evidence_score", "evidence_count", "evidence_volume"], pathway_cols + entity_cols + ["source_type"])
        with b:
            plot_phase2d_line(evidence_df, "Evidence Spike Monitoring", ["spike_score", "evidence_spike_score", "evidence_intensity", "evidence_count"], pathway_cols + entity_cols + ["source_type"])
        a, b = st.columns(2)
        with a:
            plot_phase2d_regime_timeline(evidence_df)
        with b:
            plot_phase2d_concentration(evidence_df, "Evidence Concentration", ["evidence_intensity", "evidence_score", "evidence_count", "evidence_volume"], pathway_cols + entity_cols + ["source_type"])

    with tabs[3]:
        st.subheader("Attribution Analytics")
        a, b = st.columns(2)
        with a:
            plot_phase2d_line(attribution_df, "Rolling Attribution Trends", ["rolling_contribution", "contribution_weight", "attribution_score", "component_score"], attribution_cols)
        with b:
            plot_phase2d_bar_latest(attribution_df, "Top Attribution Components", ["contribution_weight", "rolling_contribution", "attribution_score", "component_score"], attribution_cols)
        a, b = st.columns(2)
        with a:
            plot_phase2d_area(attribution_df, "Historical Explainability Evolution", ["contribution_weight", "rolling_contribution", "attribution_score", "component_score"], attribution_cols)
        with b:
            plot_phase2d_heatmap(attribution_df, "Attribution Regime / Component Heatmap", ["contribution_weight", "rolling_contribution", "attribution_score", "component_score"], attribution_cols)

    with tabs[4]:
        st.subheader("Regime Analytics")
        a, b = st.columns(2)
        with a:
            plot_phase2d_regime_timeline(regime_df)
        with b:
            plot_phase2d_regime_duration(regime_df)
        a, b = st.columns(2)
        with a:
            plot_phase2d_line(regime_df, "Regime Instability Monitoring", ["instability_score", "regime_instability", "transition_count", "acceleration_score", "acceleration_"], entity_cols + pathway_cols, zero_line=True)
        with b:
            plot_phase2d_line(regime_df, "Structural State Evolution", ["state_score", "regime_score", "structural_score", "propagation_score", "theme_score", "structural_momentum_score", "structural_momentum_"], entity_cols + pathway_cols)

    with tabs[5]:
        st.subheader("Pathway Analytics")
        a, b = st.columns(2)
        with a:
            plot_phase2d_line(pathway_df, "Pathway Stability", ["pathway_stability", "stability_score", "persistence_score", "pathway_score"], pathway_cols)
        with b:
            plot_phase2d_line(pathway_df, "Pathway Acceleration", ["pathway_acceleration", "acceleration_score", "acceleration"], pathway_cols, zero_line=True)
        a, b = st.columns(2)
        with a:
            plot_phase2d_heatmap(pathway_df, "Transmission Pathway Evolution", ["pathway_score", "stability_score", "persistence_score", "pathway_stability"], pathway_cols)
        with b:
            plot_phase2d_concentration(pathway_df, "Transmission Concentration", ["pathway_score", "stability_score", "persistence_score", "pathway_stability"], pathway_cols)

    with tabs[6]:
        st.subheader("Structural Propagation Monitoring")
        a, b = st.columns(2)
        with a:
            plot_phase2d_line(propagation_df, "Propagation Trend Analytics", ["propagation_score", "transmission_score", "structural_score", "composite_score"], entity_cols + pathway_cols)
        with b:
            plot_phase2d_concentration(propagation_df, "Structural Propagation Concentration", ["propagation_score", "transmission_score", "structural_score", "composite_score"], entity_cols + pathway_cols)
        if propagation_df.empty:
            st.info("No propagation history rows available.")
        else:
            st.markdown("### Latest Propagation Records")
            latest = propagation_df["run_date_sgt"].max() if "run_date_sgt" in propagation_df.columns else None
            latest_df = propagation_df[propagation_df["run_date_sgt"] == latest].copy() if latest is not None else propagation_df.copy()
            st.dataframe(latest_df.head(100), use_container_width=True, hide_index=True)

    with tabs[7]:
        st.subheader("Raw Phase 2D Historical Tables")
        raw_tabs = st.tabs(["Momentum", "Drivers", "Pathways", "Evidence", "Attribution", "Regime", "Propagation"])
        raw_frames = [momentum_df, driver_df, pathway_df, evidence_df, attribution_df, regime_df, propagation_df]
        for tab, frame in zip(raw_tabs, raw_frames):
            with tab:
                if frame.empty:
                    st.info("No rows available.")
                else:
                    st.dataframe(frame, use_container_width=True, hide_index=True)


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

st.title("AI Transmission Monitor v1 — Phase 2D.1")
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


# Phase 2C explainability visualization layer.
try:
    explainability_rows = fetch_phase2b_explanations(
        theme_name=selected_theme,
        limit=5000,
    )
    component_score_rows = fetch_phase2b_component_scores(
        theme_name=selected_theme,
        limit=10000,
    )
    evidence_attribution_rows = fetch_phase2b_evidence_attribution(
        theme_name=selected_theme,
        limit=10000,
    )
except Exception as exc:
    st.warning(f"Unable to load Phase 2B explainability tables: {exc}")
    explainability_rows = pd.DataFrame()
    component_score_rows = pd.DataFrame()
    evidence_attribution_rows = pd.DataFrame()

display_explainability_layer(
    explainability_rows,
    component_score_rows,
    evidence_attribution_rows,
    selected_theme=selected_theme,
    show_all_dates=show_all_theme_dates,
)

# Phase 2D.1 historical analytics visualization layer.
try:
    render_phase2d1_historical_analytics_layer(selected_theme=selected_theme)
except Exception as exc:
    st.warning(f"Unable to render Phase 2D.1 historical analytics layer: {exc}")


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
    "v1 dashboard with Phase 1 modular refactor, Phase 2C explainability visualization, and Phase 2D.1 historical analytics visualization. "
    "Legacy AI-specific views remain powered by ai_transmission_scores; generic theme scores, "
    "component decomposition and evidence attribution are read from structural theme tables."
)
