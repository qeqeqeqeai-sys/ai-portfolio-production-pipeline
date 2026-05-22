"""Dashboard O4 read-only Streamlit shell."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json

import streamlit as st

from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o4_streamlit_view_model import (
    build_dashboard_o4_view_model,
    validate_dashboard_o4_view_model,
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


def main() -> None:
    st.set_page_config(page_title="Expectation Fragility Dashboard", layout="wide")
    st.title("Expectation Fragility Dashboard (Read-Only)")

    payload = _sample_payload()
    view_model = build_dashboard_o4_view_model(deepcopy(payload))
    validation = validate_dashboard_o4_view_model(view_model)

    st.caption("Read-only deterministic visibility shell. No database writes, no recommendations, no predictive modelling.")

    kpi_cols = st.columns(4)
    for idx, (k, v) in enumerate(view_model["kpi_cards"].items()):
        kpi_cols[idx % 4].metric(k, v)

    tabs = st.tabs([p["page_title"] for p in view_model["page_registry"]])
    with tabs[0]:
        st.json(view_model["executive_overview"])
    with tabs[1]:
        st.dataframe(view_model["entity_table"], use_container_width=True)
    with tabs[2]:
        st.dataframe(view_model["subsector_table"], use_container_width=True)
    with tabs[3]:
        st.dataframe(view_model["alert_table"], use_container_width=True)
    with tabs[4]:
        st.dataframe(view_model["benchmark_table"], use_container_width=True)
    with tabs[5]:
        st.dataframe(view_model["replay_table"], use_container_width=True)
    with tabs[6]:
        st.dataframe(view_model["evidence_table"], use_container_width=True)
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
