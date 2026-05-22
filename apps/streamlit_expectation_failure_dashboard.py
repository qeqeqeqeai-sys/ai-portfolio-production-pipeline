"""Dashboard O7 read-only Streamlit shell with Supabase runtime boundary wiring."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o4_streamlit_view_model import (
    build_dashboard_o4_view_model,
    validate_dashboard_o4_view_model,
)
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o7_streamlit_supabase_runtime import (
    build_streamlit_supabase_runtime_config,
    load_streamlit_dashboard_snapshot,
)


def _sample_payload() -> dict:
    sample_path = Path("artifacts/dashboard_o1_sample_payload.json")
    if sample_path.exists():
        return json.loads(sample_path.read_text(encoding="utf-8"))
    return {
        "dashboard_entity_facts": [{"run_id": "run-001", "run_date_sgt": "2026-05-22", "entity_id": "E1", "entity_name": "Alpha", "ticker": "AAA", "subsector": "AI Apps", "composite_score": 81.0, "relative_fragility_band": "elevated", "alert_state": "watch", "benchmark_relative_label": "outlier", "evidence_quality_flag": "sufficient", "certification_status": "provisional", "replay_checksum": "x"}],
        "dashboard_subsector_facts": [{"run_id": "run-001", "run_date_sgt": "2026-05-22", "subsector": "AI Apps", "entity_count": 1, "avg_composite_score": 81.0, "fragile_entity_count": 1, "alert_entity_count": 1, "subsector_fragility_band": "elevated", "evidence_quality_summary": "sufficient", "replay_checksum": "x"}],
        "dashboard_alert_facts": [{"run_id": "run-001", "run_date_sgt": "2026-05-22", "entity_id": "E1", "ticker": "AAA", "subsector": "AI Apps", "alert_state": "watch", "alert_severity_band": "medium", "active_alert_flag": True, "dominant_alert_driver": "valuation", "evidence_quality_flag": "sufficient", "replay_checksum": "x"}],
        "dashboard_replay_facts": [{"run_id": "run-001", "replay_date_sgt": "2026-05-21", "entity_id": "E1", "ticker": "AAA", "subsector": "AI Apps", "composite_score": 77.0, "fragility_band": "elevated", "alert_state": "watch", "deterioration_label": "deteriorating", "replay_sequence": 1, "replay_checksum": "x"}],
        "dashboard_benchmark_facts": [{"run_id": "run-001", "run_date_sgt": "2026-05-22", "entity_id": "E1", "ticker": "AAA", "subsector": "AI Apps", "benchmark_id": "QQQ", "entity_fragility_score": 81.0, "benchmark_fragility_score": 62.0, "relative_gap": 19.0, "relative_gap_band": "elevated", "benchmark_relative_label": "outlier", "outlier_flag": True, "replay_checksum": "x"}],
        "dashboard_evidence_facts": [{"run_id": "run-001", "run_date_sgt": "2026-05-22", "entity_id": "E1", "ticker": "AAA", "evidence_id": "EV1", "evidence_type": "metric", "source_metric": "valuation_stretch", "source_value": 92.0, "normalized_score": 81.0, "quality_flag": "sufficient", "evidence_chain_position": 1, "template_id": "evidence_template_default", "replay_checksum": "x"}],
        "dashboard_report_metadata": {"run_id": "run-001", "run_date_sgt": "2026-05-22", "certification_status": "provisional", "report_type": "institutional_dashboard", "export_manifest_checksum": "abc"},
        "dashboard_export_manifest": {"checksum": "abc"},
    }


@st.cache_data(ttl=120)
def _load_runtime_snapshot_cached(runtime_config: dict, fallback_payload: dict):
    return load_streamlit_dashboard_snapshot(runtime_config=runtime_config, fallback_payload=fallback_payload)


def main() -> None:
    st.set_page_config(page_title="Expectation Fragility Dashboard", layout="wide")
    st.title("Expectation Fragility Dashboard (Read-Only)")

    sample_payload = _sample_payload()
    runtime_config = build_streamlit_supabase_runtime_config()
    runtime_snapshot = _load_runtime_snapshot_cached(deepcopy(runtime_config), deepcopy(sample_payload))

    mode = runtime_snapshot["mode"]
    mode_label = {
        "read_only_supabase_mode": "Read-only Supabase mode",
        "fallback_demo_mode": "Fallback/demo mode",
        "degraded_data_loading_mode": "Degraded data-loading mode",
    }.get(mode, "Fallback/demo mode")
    st.caption(f"Runtime mode: {mode_label} | refresh=manual/rerun only | cache_ttl={runtime_config['cache_ttl_seconds']}s")


    diagnostics = runtime_snapshot.get("runtime_diagnostics")
    if not diagnostics:
        diagnostics = runtime_snapshot.get("payload", {}).get("runtime_diagnostics", {})
    with st.expander("Runtime Diagnostics"):
        st.write(f"runtime_mode: {diagnostics.get('runtime_mode')}")
        st.write(f"payload_source: {diagnostics.get('payload_source')}")
        st.write(f"normalization_status: {diagnostics.get('normalization_status')}")
        st.write(f"degraded_sections: {diagnostics.get('degraded_sections')}")
        st.write(f"credentials_present: {diagnostics.get('credentials_present')}")
        st.json({"snapshot_section_statuses": diagnostics.get("snapshot_section_statuses", {})})
        st.write(f"error_message_short: {diagnostics.get('error_message_short')}")
    payload = runtime_snapshot["payload"]
    view_model = build_dashboard_o4_view_model(deepcopy(payload))
    validation = validate_dashboard_o4_view_model(view_model)

    kpi_cols = st.columns(4)
    for idx, (k, v) in enumerate(view_model["kpi_cards"].items()):
        kpi_cols[idx % 4].metric(k, v)

    tabs = st.tabs([p["page_title"] for p in view_model["page_registry"]])
    with tabs[0]: st.json(view_model["executive_overview"])
    with tabs[1]: st.dataframe(view_model["entity_table"], use_container_width=True)
    with tabs[2]: st.dataframe(view_model["subsector_table"], use_container_width=True)
    with tabs[3]: st.dataframe(view_model["alert_table"], use_container_width=True)
    with tabs[4]: st.dataframe(view_model["benchmark_table"], use_container_width=True)
    with tabs[5]: st.dataframe(view_model["replay_table"], use_container_width=True)
    with tabs[6]: st.dataframe(view_model["evidence_table"], use_container_width=True)
    with tabs[7]:
        st.subheader("Certification and Export Manifest")
        st.json(view_model["certification_panel"])
        st.json(view_model["ui_manifest"])

    st.subheader("Invariant Boundary Notes")
    st.json(view_model["invariant_flags"])
    st.subheader("View-Model Validation")
    st.json(validation)


if __name__ == "__main__":
    main()
