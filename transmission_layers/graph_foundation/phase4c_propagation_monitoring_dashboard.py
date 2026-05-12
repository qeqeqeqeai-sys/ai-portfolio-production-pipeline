import os
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
import streamlit as st
import plotly.express as px


APP_TITLE = "Phase 4C — Propagation Monitoring Dashboard"


def get_secret(name: str, default: Optional[str] = None) -> Optional[str]:
    try:
        value = st.secrets.get(name)
        if value:
            return value
    except Exception:
        pass
    return os.getenv(name, default)


SUPABASE_URL = get_secret("SUPABASE_URL")
SUPABASE_KEY = (
    get_secret("SUPABASE_SERVICE_ROLE_KEY")
    or get_secret("SUPABASE_ANON_KEY")
    or get_secret("SUPABASE_KEY")
)


class SupabaseRestClient:
    def __init__(self, url: str, key: str):
        if not url or not key:
            raise RuntimeError("Missing Supabase credentials.")
        self.base_url = url.rstrip("/") + "/rest/v1"
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

    def select(
        self,
        table: str,
        columns: str = "*",
        filters: Optional[Dict[str, str]] = None,
        order: Optional[str] = None,
        limit: int = 5000,
    ) -> List[Dict[str, Any]]:
        params = {"select": columns, "limit": str(limit)}

        if filters:
            params.update(filters)

        if order:
            params["order"] = order

        response = requests.get(
            f"{self.base_url}/{table}",
            headers=self.headers,
            params=params,
            timeout=60,
        )

        if response.status_code not in (200, 206):
            raise RuntimeError(
                f"Supabase request failed for {table}: {response.status_code}: {response.text}"
            )

        return response.json() if response.text else []


@st.cache_data(ttl=120)
def load_table_unfiltered(table: str, order: str, limit: int = 5000) -> pd.DataFrame:
    client = SupabaseRestClient(SUPABASE_URL, SUPABASE_KEY)
    rows = client.select(table, filters=None, order=order, limit=limit)
    return pd.DataFrame(rows)


def normalize_text(value: Any) -> str:
    return str(value or "").strip().lower()


def apply_anchor_theme_filter(df: pd.DataFrame, anchor_theme_name: str, theme_name: str = "") -> pd.DataFrame:
    if df.empty:
        return df

    out = df.copy()

    if "anchor_theme_name" in out.columns and anchor_theme_name:
        out = out[out["anchor_theme_name"].map(normalize_text) == normalize_text(anchor_theme_name)]

    if "theme_name" in out.columns and theme_name:
        out = out[out["theme_name"].map(normalize_text) == normalize_text(theme_name)]

    return out


def numeric(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    for col in cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def date_filter(df: pd.DataFrame, date_col: str, selected_date: Optional[str]) -> pd.DataFrame:
    if df.empty or date_col not in df.columns or not selected_date:
        return df
    return df[df[date_col].astype(str) == str(selected_date)]


def metric_card(label: str, value: Any):
    st.metric(label, value if value is not None else "—")


def show_bar(df: pd.DataFrame, x: str, y: str, title: str):
    if df.empty or x not in df.columns or y not in df.columns:
        st.info(f"No data available for {title}.")
        return
    fig = px.bar(df, x=x, y=y, title=title)
    st.plotly_chart(fig, use_container_width=True)


def show_hist(df: pd.DataFrame, x: str, title: str):
    if df.empty or x not in df.columns:
        st.info(f"No data available for {title}.")
        return
    fig = px.histogram(df, x=x, title=title)
    st.plotly_chart(fig, use_container_width=True)


def show_table(df: pd.DataFrame, columns: List[str], title: str, sort_by: Optional[str] = None, n: int = 50):
    st.subheader(title)
    if df.empty:
        st.info("No rows available.")
        return

    view = df.copy()
    if sort_by and sort_by in view.columns:
        view = view.sort_values(sort_by, ascending=False)

    existing = [c for c in columns if c in view.columns]
    st.dataframe(view[existing].head(n), use_container_width=True, hide_index=True)


def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide")

    st.title(APP_TITLE)
    st.caption(
        "Audits controlled single-hop propagation, propagation memory, snapshots, and telemetry. "
        "No recursive propagation or multi-hop analytics are performed here."
    )

    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("Missing Supabase credentials. Add SUPABASE_URL and SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY.")
        st.stop()

    with st.sidebar:
        st.header("Filters")
        anchor_theme_name = st.text_input("Anchor theme", value="ai").strip().lower()
        theme_name = st.text_input("Theme filter (optional)", value="").strip().lower()
        limit = st.number_input("Max rows per table", min_value=100, max_value=50000, value=10000, step=100)
        show_debug = st.checkbox("Show debug info", value=True)

        if st.button("Refresh data"):
            st.cache_data.clear()
            st.rerun()

    # Load unfiltered first, then filter locally.
    try:
        prop_raw = load_table_unfiltered(
            "structural_theme_graph_single_hop_propagation",
            order="run_date_sgt.desc",
            limit=int(limit),
        )
        prop_df = apply_anchor_theme_filter(prop_raw, anchor_theme_name, theme_name)
    except Exception as exc:
        st.error(f"Could not load single-hop propagation table: {exc}")
        prop_raw = pd.DataFrame()
        prop_df = pd.DataFrame()

    try:
        mem_raw = load_table_unfiltered(
            "structural_theme_graph_propagation_memory",
            order="run_date_sgt.desc",
            limit=int(limit),
        )
        mem_df = apply_anchor_theme_filter(mem_raw, anchor_theme_name, theme_name)
    except Exception as exc:
        st.warning(f"Could not load propagation memory table yet: {exc}")
        mem_raw = pd.DataFrame()
        mem_df = pd.DataFrame()

    try:
        prop_snap_raw = load_table_unfiltered(
            "structural_theme_graph_single_hop_snapshots",
            order="run_date_sgt.desc",
            limit=500,
        )
        prop_snap_df = apply_anchor_theme_filter(prop_snap_raw, anchor_theme_name, theme_name)
    except Exception as exc:
        st.warning(f"Could not load single-hop snapshots: {exc}")
        prop_snap_raw = pd.DataFrame()
        prop_snap_df = pd.DataFrame()

    try:
        mem_snap_raw = load_table_unfiltered(
            "structural_theme_graph_propagation_memory_snapshots",
            order="run_date_sgt.desc",
            limit=500,
        )
        mem_snap_df = apply_anchor_theme_filter(mem_snap_raw, anchor_theme_name, theme_name)
    except Exception as exc:
        st.warning(f"Could not load memory snapshots: {exc}")
        mem_snap_raw = pd.DataFrame()
        mem_snap_df = pd.DataFrame()

    try:
        prop_tel_df = load_table_unfiltered(
            "structural_theme_graph_single_hop_telemetry",
            order="run_date_sgt.desc",
            limit=500,
        )
    except Exception:
        prop_tel_df = pd.DataFrame()

    try:
        mem_tel_df = load_table_unfiltered(
            "structural_theme_graph_propagation_memory_telemetry",
            order="run_date_sgt.desc",
            limit=500,
        )
    except Exception:
        mem_tel_df = pd.DataFrame()

    if show_debug:
        with st.expander("Debug: raw rows loaded", expanded=False):
            st.write({
                "single_hop_raw_rows": len(prop_raw),
                "single_hop_after_filter": len(prop_df),
                "memory_raw_rows": len(mem_raw),
                "memory_after_filter": len(mem_df),
                "single_hop_snapshot_raw_rows": len(prop_snap_raw),
                "single_hop_snapshot_after_filter": len(prop_snap_df),
                "memory_snapshot_raw_rows": len(mem_snap_raw),
                "memory_snapshot_after_filter": len(mem_snap_df),
                "anchor_filter": anchor_theme_name,
                "theme_filter": theme_name,
            })

            if not prop_raw.empty and "anchor_theme_name" in prop_raw.columns:
                st.write("single_hop anchor_theme_name counts")
                st.dataframe(prop_raw["anchor_theme_name"].value_counts(dropna=False).reset_index())

            if not prop_raw.empty:
                st.write("single_hop sample")
                st.dataframe(prop_raw.head(5), use_container_width=True)

    prop_numeric_cols = [
        "source_pressure_score",
        "source_transmission_potential_score",
        "edge_strength",
        "edge_confidence_score",
        "evidence_intensity",
        "persistence_score",
        "propagation_input_score",
        "propagation_transfer_weight",
        "propagated_pressure_score",
        "propagated_positive_pressure",
        "propagated_negative_pressure",
        "bottleneck_modifier",
        "fragility_modifier",
        "saturation_modifier",
        "confidence_modifier",
    ]

    mem_numeric_cols = [
        "latest_propagated_pressure_score",
        "avg_propagated_pressure_score",
        "max_propagated_pressure_score",
        "min_propagated_pressure_score",
        "pressure_change_abs",
        "propagation_persistence_score",
        "propagation_reinforcement_score",
        "propagation_decay_score",
        "propagation_exhaustion_score",
        "carry_forward_score",
        "half_life_proxy_days",
    ]

    prop_df = numeric(prop_df, prop_numeric_cols)
    mem_df = numeric(mem_df, mem_numeric_cols)

    all_dates = set()
    if not prop_df.empty and "run_date_sgt" in prop_df.columns:
        all_dates.update(prop_df["run_date_sgt"].dropna().astype(str).unique())
    if not mem_df.empty and "run_date_sgt" in mem_df.columns:
        all_dates.update(mem_df["run_date_sgt"].dropna().astype(str).unique())

    selected_date = None
    if all_dates:
        selected_date = st.sidebar.selectbox("Run date", options=sorted(all_dates, reverse=True), index=0)

    prop_today = date_filter(prop_df, "run_date_sgt", selected_date)
    mem_today = date_filter(mem_df, "run_date_sgt", selected_date)

    st.header("Current Propagation State")

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        metric_card("Single-hop paths", len(prop_today))

    with c2:
        metric_card(
            "Avg propagated pressure",
            round(prop_today["propagated_pressure_score"].mean(), 4)
            if not prop_today.empty and "propagated_pressure_score" in prop_today.columns
            else None,
        )

    with c3:
        metric_card(
            "Watchlist paths",
            int((prop_today["propagation_status"] == "watchlist").sum())
            if not prop_today.empty and "propagation_status" in prop_today.columns
            else None,
        )

    with c4:
        metric_card("Memory paths", len(mem_today))

    with c5:
        metric_card(
            "Avg carry-forward",
            round(mem_today["carry_forward_score"].mean(), 4)
            if not mem_today.empty and "carry_forward_score" in mem_today.columns
            else None,
        )

    st.divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Single-Hop Propagation",
        "Propagation Memory",
        "Path Drilldown",
        "Snapshots",
        "Telemetry",
    ])

    with tab1:
        st.subheader("Single-Hop Propagation Overview")

        col1, col2 = st.columns(2)
        with col1:
            if not prop_today.empty and "propagation_regime" in prop_today.columns:
                counts = prop_today["propagation_regime"].value_counts().reset_index()
                counts.columns = ["propagation_regime", "count"]
                show_bar(counts, "propagation_regime", "count", "Propagation Regime Counts")
        with col2:
            if not prop_today.empty and "propagation_status" in prop_today.columns:
                counts = prop_today["propagation_status"].value_counts().reset_index()
                counts.columns = ["propagation_status", "count"]
                show_bar(counts, "propagation_status", "count", "Propagation Status Counts")

        col3, col4 = st.columns(2)
        with col3:
            show_hist(prop_today, "propagated_pressure_score", "Propagated Pressure Distribution")
        with col4:
            show_hist(prop_today, "propagation_transfer_weight", "Transfer Weight Distribution")

        show_table(
            prop_today,
            [
                "run_date_sgt",
                "source_node_key",
                "target_node_key",
                "edge_type",
                "propagated_pressure_score",
                "propagation_input_score",
                "propagation_transfer_weight",
                "propagation_direction",
                "propagation_regime",
                "propagation_status",
            ],
            "Strongest Single-Hop Paths",
            sort_by="propagated_pressure_score",
        )

    with tab2:
        st.subheader("Propagation Memory & Decay")

        if mem_today.empty:
            st.info("No memory rows available yet. Run Phase 4B after Phase 4A.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                if "memory_regime" in mem_today.columns:
                    counts = mem_today["memory_regime"].value_counts().reset_index()
                    counts.columns = ["memory_regime", "count"]
                    show_bar(counts, "memory_regime", "count", "Memory Regime Counts")
            with col2:
                if "memory_status" in mem_today.columns:
                    counts = mem_today["memory_status"].value_counts().reset_index()
                    counts.columns = ["memory_status", "count"]
                    show_bar(counts, "memory_status", "count", "Memory Status Counts")

            col3, col4 = st.columns(2)
            with col3:
                show_hist(mem_today, "carry_forward_score", "Carry-Forward Score Distribution")
            with col4:
                show_hist(mem_today, "propagation_decay_score", "Decay Score Distribution")

            show_table(
                mem_today,
                [
                    "run_date_sgt",
                    "source_node_key",
                    "target_node_key",
                    "edge_type",
                    "observation_count",
                    "latest_propagated_pressure_score",
                    "avg_propagated_pressure_score",
                    "pressure_change_abs",
                    "propagation_persistence_score",
                    "propagation_reinforcement_score",
                    "propagation_decay_score",
                    "propagation_exhaustion_score",
                    "carry_forward_score",
                    "memory_regime",
                    "memory_status",
                ],
                "Strongest Carry-Forward Paths",
                sort_by="carry_forward_score",
            )

    with tab3:
        st.subheader("Path Drilldown")

        if prop_today.empty:
            st.info("No propagation rows available.")
        else:
            path_labels = (
                prop_today["source_node_key"].astype(str)
                + " → "
                + prop_today["target_node_key"].astype(str)
                + " | "
                + prop_today["edge_type"].astype(str)
            )

            selected_idx = st.selectbox(
                "Select path",
                options=list(range(len(prop_today))),
                format_func=lambda i: path_labels.iloc[i],
            )

            row = prop_today.iloc[selected_idx]
            st.markdown("### Selected Single-Hop Path")
            st.json(row.dropna().to_dict())

            if not mem_today.empty and "propagation_key" in mem_today.columns:
                matched_mem = mem_today[mem_today["propagation_key"] == row.get("propagation_key")]
                if not matched_mem.empty:
                    st.markdown("### Matching Memory Row")
                    st.json(matched_mem.iloc[0].dropna().to_dict())
                else:
                    st.info("No matching memory row found for this path yet.")

    with tab4:
        st.subheader("Snapshot History")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Phase 4A Single-Hop Snapshots")
            if prop_snap_df.empty:
                st.info("No Phase 4A snapshots found.")
            else:
                show_table(
                    numeric(
                        prop_snap_df,
                        [
                            "propagation_rows_generated",
                            "low_propagation_count",
                            "moderate_propagation_count",
                            "high_propagation_count",
                            "avg_propagated_pressure_score",
                            "avg_transfer_weight",
                            "avg_input_score",
                        ],
                    ),
                    [
                        "run_date_sgt",
                        "snapshot_id",
                        "propagation_rows_generated",
                        "low_propagation_count",
                        "moderate_propagation_count",
                        "high_propagation_count",
                        "avg_propagated_pressure_score",
                        "avg_transfer_weight",
                        "avg_input_score",
                        "validation_status",
                    ],
                    "Single-Hop Snapshot Table",
                    n=20,
                )

        with col2:
            st.markdown("### Phase 4B Memory Snapshots")
            if mem_snap_df.empty:
                st.info("No Phase 4B snapshots found.")
            else:
                show_table(
                    numeric(
                        mem_snap_df,
                        [
                            "memory_rows_generated",
                            "persistent_count",
                            "reinforcing_count",
                            "decaying_count",
                            "insufficient_memory_count",
                            "avg_carry_forward_score",
                            "avg_decay_score",
                            "avg_reinforcement_score",
                            "avg_persistence_score",
                        ],
                    ),
                    [
                        "run_date_sgt",
                        "snapshot_id",
                        "memory_rows_generated",
                        "insufficient_memory_count",
                        "persistent_count",
                        "reinforcing_count",
                        "decaying_count",
                        "avg_carry_forward_score",
                        "avg_decay_score",
                        "avg_reinforcement_score",
                        "validation_status",
                    ],
                    "Memory Snapshot Table",
                    n=20,
                )

    with tab5:
        st.subheader("Telemetry Health")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Phase 4A Telemetry")
            if prop_tel_df.empty:
                st.info("No Phase 4A telemetry found.")
            else:
                show_table(
                    numeric(
                        prop_tel_df,
                        [
                            "runtime_seconds",
                            "source_edges_read",
                            "pressure_rows_read",
                            "transmission_rows_read",
                            "propagation_rows_upserted",
                        ],
                    ),
                    [
                        "run_date_sgt",
                        "pipeline_name",
                        "status",
                        "source_edges_read",
                        "pressure_rows_read",
                        "transmission_rows_read",
                        "propagation_rows_upserted",
                        "validation_status",
                        "validation_error_count",
                        "validation_warning_count",
                        "runtime_seconds",
                        "error_message",
                    ],
                    "Single-Hop Telemetry",
                    n=20,
                )

        with col2:
            st.markdown("### Phase 4B Telemetry")
            if mem_tel_df.empty:
                st.info("No Phase 4B telemetry found.")
            else:
                show_table(
                    numeric(mem_tel_df, ["runtime_seconds", "propagation_rows_read", "memory_rows_upserted"]),
                    [
                        "run_date_sgt",
                        "pipeline_name",
                        "status",
                        "propagation_rows_read",
                        "memory_rows_upserted",
                        "validation_status",
                        "validation_error_count",
                        "validation_warning_count",
                        "runtime_seconds",
                        "error_message",
                    ],
                    "Memory Telemetry",
                    n=20,
                )


if __name__ == "__main__":
    main()
