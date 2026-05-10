import os
import requests
import pandas as pd
import streamlit as st
from datetime import date, timedelta
from zoneinfo import ZoneInfo


# =====================================================
# CONFIG
# =====================================================

st.set_page_config(
    page_title="AI Transmission Monitoring",
    page_icon="📡",
    layout="wide",
)

SGT = ZoneInfo("Asia/Singapore")

SUPABASE_URL = (
    st.secrets.get("SUPABASE_URL", None)
    or os.getenv("SUPABASE_URL")
)

SUPABASE_ANON_KEY = (
    st.secrets.get("SUPABASE_ANON_KEY", None)
    or os.getenv("SUPABASE_ANON_KEY")
    or os.getenv("SUPABASE_KEY")
)

THEME_NAME = "ai"

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    st.error(
        "Missing Supabase credentials. Add SUPABASE_URL and SUPABASE_ANON_KEY "
        "to Streamlit secrets or environment variables."
    )
    st.stop()

HEADERS = {
    "apikey": SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    "Content-Type": "application/json",
}


# =====================================================
# REST HELPERS
# =====================================================

@st.cache_data(ttl=300)
def supabase_get(table: str, params: dict | None = None) -> pd.DataFrame:
    url = f"{SUPABASE_URL}/rest/v1/{table}"

    response = requests.get(
        url,
        headers=HEADERS,
        params=params or {},
        timeout=45,
    )

    if response.status_code >= 400:
        st.error(f"Supabase query failed for {table}: {response.status_code}")
        st.code(response.text)
        return pd.DataFrame()

    return pd.DataFrame(response.json())


def safe_numeric(df: pd.DataFrame, col: str) -> pd.Series:
    if df.empty or col not in df.columns:
        return pd.Series(dtype="float64")
    return pd.to_numeric(df[col], errors="coerce")


def format_status_badge(status: str) -> str:
    status = str(status or "UNKNOWN").upper()

    if status in ["SUCCESS", "PASS"]:
        return "🟢 " + status
    if status in ["WARN", "WARNING", "FAILED_VALIDATION"]:
        return "🟠 " + status
    if status in ["FAIL", "ERROR"]:
        return "🔴 " + status

    return "⚪ " + status


def drift_status(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "⚪ UNKNOWN"

    abs_value = abs(value)

    if abs_value < 5:
        return "🟢 NORMAL"
    if abs_value < 15:
        return "🟠 ELEVATED"

    return "🔴 CRITICAL"


def runtime_status(runtime: float | None, avg_runtime: float | None) -> str:
    if runtime is None or avg_runtime is None or pd.isna(runtime) or pd.isna(avg_runtime):
        return "⚪ UNKNOWN"

    if avg_runtime == 0:
        return "🟢 NORMAL"

    ratio = runtime / avg_runtime

    if ratio < 1.5:
        return "🟢 NORMAL"
    if ratio < 2.5:
        return "🟠 ELEVATED"

    return "🔴 CRITICAL"


def style_validation_table(df: pd.DataFrame):
    def style_row(row):
        status = str(row.get("status", row.get("status_display", ""))).upper()
        severity = str(row.get("severity", "")).upper()

        if "FAIL" in status:
            color = "background-color: #ffdddd"
        elif "WARN" in status or "WARNING" in severity:
            color = "background-color: #fff2cc"
        elif "PASS" in status:
            color = "background-color: #ddffdd"
        else:
            color = ""

        return [color for _ in row]

    return df.style.apply(style_row, axis=1)


# =====================================================
# DATA LOADERS
# =====================================================

@st.cache_data(ttl=300)
def load_telemetry(days: int = 30) -> pd.DataFrame:
    start_date = (date.today() - timedelta(days=days)).isoformat()

    params = {
        "theme_name": f"eq.{THEME_NAME}",
        "run_date_sgt": f"gte.{start_date}",
        "select": "*",
        "order": "run_timestamp_sgt.desc",
        "limit": "1000",
    }

    df = supabase_get("structural_theme_pipeline_telemetry", params)

    if df.empty:
        return df

    numeric_cols = [
        "runtime_seconds",
        "score_rows",
        "observation_rows",
        "validation_failures",
        "validation_warnings",
        "avg_score",
        "min_score",
        "max_score",
        "avg_confidence",
        "bullish_count",
        "bearish_count",
        "neutral_count",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "run_timestamp_sgt" in df.columns:
        df["run_timestamp_sgt"] = pd.to_datetime(df["run_timestamp_sgt"], errors="coerce")

    if "run_date_sgt" in df.columns:
        df["run_date_sgt"] = pd.to_datetime(df["run_date_sgt"], errors="coerce").dt.date

    return df


@st.cache_data(ttl=300)
def load_validation(days: int = 30) -> pd.DataFrame:
    start_date = (date.today() - timedelta(days=days)).isoformat()

    params = {
        "theme_name": f"eq.{THEME_NAME}",
        "run_date_sgt": f"gte.{start_date}",
        "select": "*",
        "order": "run_timestamp_sgt.desc",
        "limit": "5000",
    }

    df = supabase_get("structural_theme_validation_results", params)

    if df.empty:
        return df

    if "run_timestamp_sgt" in df.columns:
        df["run_timestamp_sgt"] = pd.to_datetime(df["run_timestamp_sgt"], errors="coerce")

    if "run_date_sgt" in df.columns:
        df["run_date_sgt"] = pd.to_datetime(df["run_date_sgt"], errors="coerce").dt.date

    return df


# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.title("📡 Monitoring Controls")

days = st.sidebar.selectbox(
    "Lookback window",
    options=[7, 14, 30, 60, 90],
    index=2,
)

refresh = st.sidebar.button("Refresh data")

if refresh:
    st.cache_data.clear()
    st.rerun()


telemetry_df = load_telemetry(days)
validation_df = load_validation(days)


# =====================================================
# HEADER
# =====================================================

st.title("📡 AI Transmission Monitoring Dashboard")
st.caption(
    "Phase 2A monitoring layer for pipeline health, validation results, runtime trends, "
    "score drift, evidence coverage, and recent failures."
)

if telemetry_df.empty and validation_df.empty:
    st.warning("No Phase 2A telemetry or validation records found yet.")
    st.stop()


# =====================================================
# PREP
# =====================================================

telemetry_sorted = telemetry_df.sort_values("run_timestamp_sgt") if not telemetry_df.empty else pd.DataFrame()
latest = telemetry_df.iloc[0] if not telemetry_df.empty else None

latest_warning = pd.DataFrame()
latest_failure = pd.DataFrame()
latest_pipeline_error = pd.DataFrame()

if not validation_df.empty:
    latest_warning = validation_df[
        validation_df["status"].astype(str).str.upper() == "WARN"
    ].head(1)

    latest_failure = validation_df[
        validation_df["status"].astype(str).str.upper() == "FAIL"
    ].head(1)

if not telemetry_df.empty:
    latest_pipeline_error = telemetry_df[
        telemetry_df["status"].astype(str).str.upper().isin(
            ["ERROR", "FAILED_VALIDATION", "FAIL"]
        )
    ].head(1)


# =====================================================
# 1. PIPELINE HEALTH
# =====================================================

st.subheader("1. Pipeline Health")

if latest is not None:
    col1, col2, col3, col4, col5 = st.columns(5)

    latest_status = latest.get("status", "UNKNOWN")
    runtime_seconds = latest.get("runtime_seconds", None)
    score_rows = latest.get("score_rows", None)
    observation_rows = latest.get("observation_rows", None)
    validation_failures = latest.get("validation_failures", 0)
    validation_warnings = latest.get("validation_warnings", 0)

    with col1:
        st.metric("Latest Status", format_status_badge(latest_status))

    with col2:
        st.metric(
            "Runtime",
            f"{runtime_seconds:.1f}s" if pd.notna(runtime_seconds) else "N/A",
        )

    with col3:
        st.metric(
            "Score Rows",
            int(score_rows) if pd.notna(score_rows) else "N/A",
        )

    with col4:
        st.metric(
            "Evidence Rows",
            int(observation_rows) if pd.notna(observation_rows) else "N/A",
        )

    with col5:
        st.metric(
            "Validation Issues",
            f"{int(validation_failures or 0)} fail / {int(validation_warnings or 0)} warn",
        )

    # -------------------------------------------------
    # Trend Sparklines
    # -------------------------------------------------

    st.markdown("#### Quick Trend Sparklines")

    spark_cols = st.columns(4)

    if not telemetry_sorted.empty:
        with spark_cols[0]:
            st.caption("Runtime")
            if "runtime_seconds" in telemetry_sorted.columns:
                st.line_chart(
                    telemetry_sorted,
                    x="run_timestamp_sgt",
                    y="runtime_seconds",
                    height=120,
                )

        with spark_cols[1]:
            st.caption("Score Rows")
            if "score_rows" in telemetry_sorted.columns:
                st.line_chart(
                    telemetry_sorted,
                    x="run_timestamp_sgt",
                    y="score_rows",
                    height=120,
                )

        with spark_cols[2]:
            st.caption("Evidence Rows")
            if "observation_rows" in telemetry_sorted.columns:
                st.line_chart(
                    telemetry_sorted,
                    x="run_timestamp_sgt",
                    y="observation_rows",
                    height=120,
                )

        with spark_cols[3]:
            st.caption("Warnings")
            if "validation_warnings" in telemetry_sorted.columns:
                st.line_chart(
                    telemetry_sorted,
                    x="run_timestamp_sgt",
                    y="validation_warnings",
                    height=120,
                )

    # -------------------------------------------------
    # Latest Failure / Warning Cards
    # -------------------------------------------------

    st.markdown("#### Latest Operational Signals")

    signal_col1, signal_col2, signal_col3 = st.columns(3)

    with signal_col1:
        st.markdown("##### Latest Pipeline Error")
        if latest_pipeline_error.empty:
            st.success("No recent pipeline error.")
        else:
            err = latest_pipeline_error.iloc[0]
            st.error(str(err.get("error_message", "Pipeline error detected.")))

    with signal_col2:
        st.markdown("##### Latest Validation Failure")
        if latest_failure.empty:
            st.success("No validation failure.")
        else:
            fail = latest_failure.iloc[0]
            st.error(
                f"{fail.get('validation_name', 'Unknown validation')} — "
                f"{fail.get('message', '')}"
            )

    with signal_col3:
        st.markdown("##### Latest Warning")
        if latest_warning.empty:
            st.success("No warning.")
        else:
            warn = latest_warning.iloc[0]
            st.warning(
                f"{warn.get('validation_name', 'Unknown warning')} — "
                f"{warn.get('message', '')}"
            )

    with st.expander("Latest run metadata"):
        metadata_cols = [
            "run_timestamp_sgt",
            "run_date_sgt",
            "pipeline_name",
            "theme_name",
            "github_run_id",
            "github_workflow",
            "github_repository",
            "github_branch",
            "error_message",
        ]

        existing_cols = [c for c in metadata_cols if c in telemetry_df.columns]

        st.dataframe(
            telemetry_df[existing_cols].head(1),
            use_container_width=True,
            hide_index=True,
        )


# =====================================================
# 2. VALIDATION RESULTS
# =====================================================

st.subheader("2. Validation Results")

if validation_df.empty:
    st.info("No validation records found.")
else:
    col1, col2, col3, col4 = st.columns(4)

    total_checks = len(validation_df)
    fail_count = len(validation_df[validation_df["status"].astype(str).str.upper() == "FAIL"])
    warn_count = len(validation_df[validation_df["status"].astype(str).str.upper() == "WARN"])
    pass_count = len(validation_df[validation_df["status"].astype(str).str.upper() == "PASS"])

    with col1:
        st.metric("Total Checks", total_checks)

    with col2:
        st.metric("Passed", pass_count)

    with col3:
        st.metric("Warnings", warn_count)

    with col4:
        st.metric("Failures", fail_count)

    validation_display = validation_df.copy()

    if "status" in validation_display.columns:
        validation_display["status_display"] = validation_display["status"].apply(format_status_badge)

    show_cols = [
        "run_timestamp_sgt",
        "validation_name",
        "severity",
        "status",
        "status_display",
        "observed_value",
        "expected_value",
        "message",
    ]

    show_cols = [c for c in show_cols if c in validation_display.columns]

    st.dataframe(
        style_validation_table(validation_display[show_cols].head(100)),
        use_container_width=True,
        hide_index=True,
    )


# =====================================================
# 3. RUNTIME TRENDS + STABILITY
# =====================================================

st.subheader("3. Runtime Trends & Stability")

if telemetry_df.empty:
    st.info("No telemetry records found.")
else:
    runtime_df = telemetry_sorted.copy()

    if "runtime_seconds" in runtime_df.columns:
        runtime_df["runtime_rolling_avg"] = runtime_df["runtime_seconds"].rolling(
            window=5,
            min_periods=1,
        ).mean()

        runtime_df["runtime_rolling_std"] = runtime_df["runtime_seconds"].rolling(
            window=5,
            min_periods=2,
        ).std()

        st.line_chart(
            runtime_df,
            x="run_timestamp_sgt",
            y=["runtime_seconds", "runtime_rolling_avg"],
        )

    col1, col2, col3, col4 = st.columns(4)

    runtime_series = safe_numeric(runtime_df, "runtime_seconds").dropna()

    avg_runtime = runtime_series.mean() if not runtime_series.empty else None
    max_runtime = runtime_series.max() if not runtime_series.empty else None
    latest_runtime = runtime_series.iloc[-1] if not runtime_series.empty else None
    runtime_vol = runtime_series.std() if len(runtime_series) >= 2 else None

    with col1:
        st.metric(
            "Average Runtime",
            f"{avg_runtime:.1f}s" if avg_runtime is not None and pd.notna(avg_runtime) else "N/A",
        )

    with col2:
        st.metric(
            "Max Runtime",
            f"{max_runtime:.1f}s" if max_runtime is not None and pd.notna(max_runtime) else "N/A",
        )

    with col3:
        st.metric(
            "Latest Runtime",
            f"{latest_runtime:.1f}s" if latest_runtime is not None and pd.notna(latest_runtime) else "N/A",
        )

    with col4:
        st.metric(
            "Runtime Stability",
            runtime_status(latest_runtime, avg_runtime),
        )

    if runtime_vol is not None and pd.notna(runtime_vol):
        st.caption(f"Runtime volatility over selected window: {runtime_vol:.2f}s")


# =====================================================
# 4. SCORE DRIFT
# =====================================================

st.subheader("4. Score Drift")

if telemetry_df.empty:
    st.info("No telemetry records found.")
else:
    drift_df = telemetry_sorted.copy()

    score_cols = [
        c for c in ["avg_score", "min_score", "max_score", "avg_confidence"]
        if c in drift_df.columns
    ]

    if score_cols:
        st.line_chart(
            drift_df,
            x="run_timestamp_sgt",
            y=score_cols,
        )

        avg_score_series = safe_numeric(drift_df, "avg_score").dropna()

        latest_avg_score = avg_score_series.iloc[-1] if not avg_score_series.empty else None

        if len(avg_score_series) >= 2:
            one_run_drift = avg_score_series.iloc[-1] - avg_score_series.iloc[-2]
        else:
            one_run_drift = None

        if len(avg_score_series) >= 5:
            rolling_mean = avg_score_series.rolling(window=5, min_periods=1).mean()
            rolling_drift = avg_score_series.iloc[-1] - rolling_mean.iloc[-1]
        else:
            rolling_drift = one_run_drift

        latest_conf_series = safe_numeric(drift_df, "avg_confidence").dropna()
        latest_conf_value = latest_conf_series.iloc[-1] if not latest_conf_series.empty else None

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Latest Avg Score",
                f"{latest_avg_score:.2f}" if latest_avg_score is not None and pd.notna(latest_avg_score) else "N/A",
            )

        with col2:
            st.metric(
                "1-Run Score Change",
                f"{one_run_drift:.2f}" if one_run_drift is not None and pd.notna(one_run_drift) else "N/A",
            )

        with col3:
            st.metric(
                "Drift Status",
                drift_status(rolling_drift),
            )

        with col4:
            st.metric(
                "Latest Avg Confidence",
                f"{latest_conf_value:.2f}" if latest_conf_value is not None and pd.notna(latest_conf_value) else "N/A",
            )

        if rolling_drift is not None and pd.notna(rolling_drift):
            if abs(rolling_drift) >= 15:
                st.error(f"Critical score drift detected: {rolling_drift:.2f}")
            elif abs(rolling_drift) >= 5:
                st.warning(f"Elevated score drift detected: {rolling_drift:.2f}")
            else:
                st.success(f"Score drift normal: {rolling_drift:.2f}")
    else:
        st.info("Score drift fields not available yet.")


# =====================================================
# 5. EVIDENCE COVERAGE
# =====================================================

st.subheader("5. Evidence Coverage")

if telemetry_df.empty:
    st.info("No telemetry records found.")
else:
    evidence_df = telemetry_sorted.copy()

    if "score_rows" in evidence_df.columns and "observation_rows" in evidence_df.columns:
        evidence_df["evidence_per_score"] = (
            pd.to_numeric(evidence_df["observation_rows"], errors="coerce")
            / pd.to_numeric(evidence_df["score_rows"], errors="coerce").replace(0, pd.NA)
        )

        st.line_chart(
            evidence_df,
            x="run_timestamp_sgt",
            y=["score_rows", "observation_rows"],
        )

        col1, col2, col3 = st.columns(3)

        latest_score_rows = safe_numeric(evidence_df, "score_rows").dropna()
        latest_obs_rows = safe_numeric(evidence_df, "observation_rows").dropna()
        latest_ratio = pd.to_numeric(evidence_df["evidence_per_score"], errors="coerce").dropna()

        with col1:
            st.metric(
                "Latest Score Rows",
                int(latest_score_rows.iloc[-1]) if not latest_score_rows.empty else "N/A",
            )

        with col2:
            st.metric(
                "Latest Evidence Rows",
                int(latest_obs_rows.iloc[-1]) if not latest_obs_rows.empty else "N/A",
            )

        with col3:
            st.metric(
                "Evidence / Score",
                f"{latest_ratio.iloc[-1]:.2f}" if not latest_ratio.empty else "N/A",
            )

        st.line_chart(
            evidence_df,
            x="run_timestamp_sgt",
            y="evidence_per_score",
        )

        if not latest_ratio.empty:
            ratio_value = latest_ratio.iloc[-1]

            if ratio_value < 0.25:
                st.warning("Evidence coverage is thin relative to score rows.")
            elif ratio_value > 20:
                st.warning("Evidence coverage is unusually high. Check for duplicate evidence ingestion.")
            else:
                st.success("Evidence coverage looks healthy.")
    else:
        st.info("Evidence coverage fields not available yet.")


# =====================================================
# 6. RECENT FAILURES
# =====================================================

st.subheader("6. Recent Failures")

failure_tabs = st.tabs(["Pipeline Errors", "Validation Failures", "Warnings"])

with failure_tabs[0]:
    if telemetry_df.empty:
        st.info("No telemetry records found.")
    else:
        error_df = telemetry_df[
            telemetry_df["status"].astype(str).str.upper().isin(
                ["ERROR", "FAILED_VALIDATION", "FAIL"]
            )
        ].copy()

        if error_df.empty:
            st.success("No recent pipeline errors found.")
        else:
            cols = [
                "run_timestamp_sgt",
                "status",
                "runtime_seconds",
                "score_rows",
                "observation_rows",
                "validation_failures",
                "validation_warnings",
                "error_message",
                "github_run_id",
            ]

            cols = [c for c in cols if c in error_df.columns]

            st.dataframe(
                error_df[cols].head(50),
                use_container_width=True,
                hide_index=True,
            )

with failure_tabs[1]:
    if validation_df.empty:
        st.info("No validation records found.")
    else:
        fail_df = validation_df[
            validation_df["status"].astype(str).str.upper() == "FAIL"
        ].copy()

        if fail_df.empty:
            st.success("No validation failures found.")
        else:
            cols = [
                "run_timestamp_sgt",
                "validation_name",
                "severity",
                "observed_value",
                "expected_value",
                "message",
            ]

            cols = [c for c in cols if c in fail_df.columns]

            st.dataframe(
                style_validation_table(fail_df[cols].head(100)),
                use_container_width=True,
                hide_index=True,
            )

with failure_tabs[2]:
    if validation_df.empty:
        st.info("No validation records found.")
    else:
        warn_df = validation_df[
            validation_df["status"].astype(str).str.upper() == "WARN"
        ].copy()

        if warn_df.empty:
            st.success("No validation warnings found.")
        else:
            cols = [
                "run_timestamp_sgt",
                "validation_name",
                "severity",
                "observed_value",
                "expected_value",
                "message",
            ]

            cols = [c for c in cols if c in warn_df.columns]

            st.dataframe(
                style_validation_table(warn_df[cols].head(100)),
                use_container_width=True,
                hide_index=True,
            )


# =====================================================
# RAW DATA
# =====================================================

with st.expander("Raw Phase 2A telemetry data"):
    if telemetry_df.empty:
        st.info("No telemetry data.")
    else:
        st.dataframe(
            telemetry_df,
            use_container_width=True,
            hide_index=True,
        )

with st.expander("Raw Phase 2A validation data"):
    if validation_df.empty:
        st.info("No validation data.")
    else:
        st.dataframe(
            validation_df,
            use_container_width=True,
            hide_index=True,
        )
