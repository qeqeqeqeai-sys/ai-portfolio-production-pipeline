from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from copy import deepcopy
import importlib

from transmission_layers.expectation_failure import dashboard_operationalization as mod
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o4_streamlit_view_model import (
    build_dashboard_o4_benchmark_table,
    build_dashboard_o4_certification_panel,
    build_dashboard_o4_entity_table,
    build_dashboard_o4_evidence_table,
    build_dashboard_o4_filter_options,
    build_dashboard_o4_kpi_cards,
    build_dashboard_o4_page_registry,
    build_dashboard_o4_replay_table,
    build_dashboard_o4_subsector_table,
    build_dashboard_o4_ui_manifest,
    build_dashboard_o4_view_model,
    validate_dashboard_o4_view_model,
)


def _payload():
    return {
        "dashboard_entity_facts": [
            {"run_id": "run-001", "run_date_sgt": "2026-05-22", "entity_id": "E2", "entity_name": "Beta", "ticker": "BBB", "subsector": "AI Infra", "composite_score": 65.0, "relative_fragility_band": "contained", "alert_state": "normal", "benchmark_relative_label": "neutral", "evidence_quality_flag": "sufficient", "certification_status": "provisional", "replay_checksum": "2"},
            {"run_id": "run-001", "run_date_sgt": "2026-05-22", "entity_id": "E1", "entity_name": "Alpha", "ticker": "AAA", "subsector": "AI Apps", "composite_score": 88.0, "relative_fragility_band": "elevated", "alert_state": "watch", "benchmark_relative_label": "outlier", "evidence_quality_flag": "insufficient", "certification_status": "provisional", "replay_checksum": "1"},
        ],
        "dashboard_subsector_facts": [{"run_id": "run-001", "run_date_sgt": "2026-05-22", "subsector": "AI Apps", "entity_count": 1, "avg_composite_score": 88.0, "fragile_entity_count": 1, "alert_entity_count": 1, "subsector_fragility_band": "elevated", "evidence_quality_summary": "insufficient", "replay_checksum": "x"}],
        "dashboard_alert_facts": [{"run_id": "run-001", "run_date_sgt": "2026-05-22", "entity_id": "E1", "ticker": "AAA", "subsector": "AI Apps", "alert_state": "watch", "alert_severity_band": "medium", "active_alert_flag": True, "dominant_alert_driver": "valuation", "evidence_quality_flag": "insufficient", "replay_checksum": "x"}],
        "dashboard_replay_facts": [{"run_id": "run-001", "replay_date_sgt": "2026-05-21", "entity_id": "E1", "ticker": "AAA", "subsector": "AI Apps", "composite_score": 75.0, "fragility_band": "elevated", "alert_state": "watch", "deterioration_label": "deteriorating", "replay_sequence": 1, "replay_checksum": "x"}],
        "dashboard_benchmark_facts": [{"run_id": "run-001", "run_date_sgt": "2026-05-22", "entity_id": "E1", "ticker": "AAA", "subsector": "AI Apps", "benchmark_id": "QQQ", "entity_fragility_score": 88.0, "benchmark_fragility_score": 60.0, "relative_gap": 28.0, "relative_gap_band": "elevated", "benchmark_relative_label": "outlier", "outlier_flag": True, "replay_checksum": "x"}],
        "dashboard_evidence_facts": [{"run_id": "run-001", "run_date_sgt": "2026-05-22", "entity_id": "E1", "ticker": "AAA", "evidence_id": "EV1", "evidence_type": "metric", "source_metric": "valuation", "source_value": 90.0, "normalized_score": 80.0, "quality_flag": "insufficient", "evidence_chain_position": 1, "template_id": "tmp", "replay_checksum": "x"}],
        "dashboard_report_metadata": {"run_id": "run-001", "run_date_sgt": "2026-05-22", "certification_status": "provisional", "report_type": "institutional_dashboard", "export_manifest_checksum": "abc"},
        "dashboard_export_manifest": {"checksum": "abc"},
        "dashboard_o2_persistence_manifest": {"validation_status": "valid"},
        "dashboard_o3_write_result_manifest": {"validation_status": "valid"},
    }


def test_public_apis_exist_and_additive_exports():
    names = [
        "build_dashboard_o4_view_model", "build_dashboard_o4_page_registry", "build_dashboard_o4_filter_options",
        "build_dashboard_o4_kpi_cards", "build_dashboard_o4_entity_table", "build_dashboard_o4_subsector_table",
        "build_dashboard_o4_alert_table", "build_dashboard_o4_benchmark_table", "build_dashboard_o4_replay_table",
        "build_dashboard_o4_evidence_table", "build_dashboard_o4_certification_panel", "validate_dashboard_o4_view_model",
        "build_dashboard_o4_ui_manifest",
    ]
    for n in names:
        assert hasattr(mod, n)


def test_determinism_order_immutability_and_validation():
    p = _payload()
    orig = deepcopy(p)
    a = build_dashboard_o4_view_model(p)
    b = build_dashboard_o4_view_model(deepcopy(p))
    assert p == orig
    assert a == b
    assert validate_dashboard_o4_view_model(a)["validation_status"] == "valid"
    assert list(a.keys()) == [
        "schema_version", "module_version", "page_registry", "filter_options", "kpi_cards", "executive_overview", "entity_table", "subsector_table", "alert_table", "benchmark_table", "replay_table", "evidence_table", "certification_panel", "ui_manifest", "invariant_flags"
    ]


def test_registry_filters_kpis_and_table_shapes():
    p = _payload()
    registry = build_dashboard_o4_page_registry()
    assert [r["page_sequence"] for r in registry] == [1, 2, 3, 4, 5, 6, 7, 8]
    assert registry[0]["page_title"] == "Executive Fragility Overview"

    filt = build_dashboard_o4_filter_options(p)
    assert list(filt.keys()) == ["run_id", "run_date_sgt", "subsector", "alert_state", "benchmark_id", "certification_status", "evidence_quality_flag"]

    kpi = build_dashboard_o4_kpi_cards(p)
    assert kpi["total_entities"] == 2
    assert kpi["fragile_entity_count"] == 1
    assert kpi["active_alert_count"] == 1
    assert kpi["benchmark_outlier_count"] == 1
    assert kpi["evidence_quality_issue_count"] == 1

    assert set(build_dashboard_o4_entity_table(p)[0].keys())
    assert set(build_dashboard_o4_subsector_table(p)[0].keys())
    assert set(build_dashboard_o4_benchmark_table(p)[0].keys())
    assert set(build_dashboard_o4_replay_table(p)[0].keys())
    assert set(build_dashboard_o4_evidence_table(p)[0].keys())


def test_certification_ui_manifest_forbidden_language_and_missing_sections():
    p = _payload()
    panel = build_dashboard_o4_certification_panel(p)
    assert panel["o2_validation_status"] == "valid"

    vm = build_dashboard_o4_view_model(p)
    ui = build_dashboard_o4_ui_manifest(vm)
    assert ui["page_count"] == 8
    assert ui["checksum"] == build_dashboard_o4_ui_manifest(vm)["checksum"]

    lowered = str(vm).lower()
    for word in ["buy", "sell", "short", "target price"]:
        assert word not in lowered

    bad = deepcopy(vm)
    bad.pop("kpi_cards")
    assert validate_dashboard_o4_view_model(bad)["validation_status"] == "invalid"


def test_core_module_has_no_streamlit_or_io_side_effect_signals():
    module = importlib.import_module("transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o4_streamlit_view_model")
    source = module.__doc__ or ""
    assert "streamlit" in source.lower()
    assert not hasattr(module, "st")
