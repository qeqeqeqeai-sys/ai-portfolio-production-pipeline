from copy import deepcopy

from transmission_layers.expectation_failure import dashboard_operationalization as mod
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o1_export_schema import (
    build_dashboard_o1_export_payload,
)


def _sample_inputs():
    return {
        "run_id": "run-001",
        "run_date_sgt": "2026-05-22",
        "entity_rows": [
            {"entity_id": "E2", "entity_name": "Beta", "ticker": "BBB", "subsector": "AI Infra", "composite_score": 120, "valuation_stretch_score": -1, "fundamental_support_score": 23, "narrative_saturation_score": 11, "certainty_fragility_score": 77, "structural_weakness_score": 44, "relative_fragility_rank": 2, "alert_state": "watch"},
            {"entity_id": "E1", "entity_name": "Alpha", "ticker": "AAA", "subsector": "AI Apps", "composite_score": 88},
        ],
        "alert_rows": [{"entity_id": "E1", "ticker": "AAA", "subsector": "AI Apps", "alert_state": "watch", "active_alert_flag": 1}],
        "replay_rows": [{"entity_id": "E1", "ticker": "AAA", "subsector": "AI Apps", "replay_sequence": 2, "replay_date_sgt": "2026-05-21", "composite_score": 55}],
        "benchmark_rows": [{"entity_id": "E1", "ticker": "AAA", "subsector": "AI Apps", "benchmark_id": "QQQ", "entity_fragility_score": 84, "benchmark_fragility_score": 50, "relative_gap": 34}],
        "evidence_rows": [{"entity_id": "E1", "ticker": "AAA", "evidence_id": "EV1", "source_metric": "pe_ratio", "source_value": 222, "normalized_score": 150, "evidence_chain_position": 1}],
        "generated_at_sgt": "2026-05-22T12:00:00+08:00",
    }


def test_public_apis_exist():
    for name in [
        "build_dashboard_entity_facts",
        "build_dashboard_subsector_facts",
        "build_dashboard_alert_facts",
        "build_dashboard_replay_facts",
        "build_dashboard_benchmark_facts",
        "build_dashboard_evidence_facts",
        "build_dashboard_report_metadata",
        "build_dashboard_export_manifest",
        "build_dashboard_o1_export_payload",
    ]:
        assert hasattr(mod, name)


def test_payload_determinism_and_order_and_checksums_and_streamlit_shape():
    kwargs = _sample_inputs()
    a = build_dashboard_o1_export_payload(**deepcopy(kwargs))
    b = build_dashboard_o1_export_payload(**deepcopy(kwargs))
    assert a == b
    assert list(a.keys()) == [
        "dashboard_entity_facts",
        "dashboard_subsector_facts",
        "dashboard_alert_facts",
        "dashboard_replay_facts",
        "dashboard_benchmark_facts",
        "dashboard_evidence_facts",
        "dashboard_report_metadata",
        "dashboard_export_manifest",
    ]
    assert a["dashboard_export_manifest"]["checksum"] == b["dashboard_export_manifest"]["checksum"]
    for key in list(a.keys())[:6]:
        assert isinstance(a[key], list)
        assert all(isinstance(r, dict) for r in a[key])


def test_field_order_fallback_immutability_sorting_and_bounding():
    kwargs = _sample_inputs()
    orig = deepcopy(kwargs)
    payload = build_dashboard_o1_export_payload(**kwargs)
    assert kwargs == orig

    entity = payload["dashboard_entity_facts"]
    assert entity[0]["entity_id"] == "E2"  # sorted composite desc
    assert entity[0]["composite_score"] == 100.0
    assert entity[0]["valuation_stretch_score"] == 0.0
    assert entity[0]["benchmark_relative_label"] == "neutral"
    assert list(entity[0].keys())[0:3] == ["run_id", "run_date_sgt", "entity_id"]

    evidence = payload["dashboard_evidence_facts"][0]
    assert evidence["source_value"] == 100.0
    assert evidence["normalized_score"] == 100.0


def test_manifest_counts_no_forbidden_language_and_existing_exports_still_work():
    kwargs = _sample_inputs()
    payload = build_dashboard_o1_export_payload(**kwargs)
    counts = payload["dashboard_export_manifest"]["record_counts"]
    assert counts["dashboard_entity_facts"] == len(payload["dashboard_entity_facts"])
    assert payload["dashboard_report_metadata"]["entity_fact_count"] == len(payload["dashboard_entity_facts"])

    text = str(payload).lower()
    for forbidden in ["buy", "sell", "short", "target price", "portfolio allocation", "backtesting", "predictive", "trade recommendation"]:
        assert forbidden not in text

    from transmission_layers.expectation_failure import build_phase_a1_expectation_failure_contract_report

    report = build_phase_a1_expectation_failure_contract_report()
    assert "defined_scores" in report
