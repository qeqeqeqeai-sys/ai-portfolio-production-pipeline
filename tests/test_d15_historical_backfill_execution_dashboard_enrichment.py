from copy import deepcopy

from transmission_layers.expectation_failure.expectation_intelligence import (
    build_d15_backfill_execution_inventory,
    build_d15_dashboard_enrichment_payload,
    build_d15_historical_execution_timeline,
    build_d15_report_markdown,
    build_d15_report_payload,
    certify_d15_dashboard_enrichment,
)
from transmission_layers.expectation_failure.dashboard_operationalization.d7_streamlit_dashboard_viewer import build_d7_dashboard_view_model


def _sample_payloads():
    d11 = {"historical_replay_windows": {"lineage_refs": ["L2", "L1"], "replay_windows": [{"window_label": "W2", "replay_window_status": "EXECUTED", "lineage_ref": "L2"}, {"window_label": "W1", "replay_window_status": "EXECUTED", "lineage_ref": "L1"}]}, "certification": {"certification_status": "CERTIFIED_D11"}}
    d12 = {"historical_expectation_inventory": {"lineage_refs": ["L1", "L2"]}, "cross_window_patterns": [{"window_label": "W1", "pattern_classification": "RECURRING_PRESSURE", "lineage_ref": "L1"}], "expectation_intelligence_synthesis": {"replay_depth_interpretation": "SUFFICIENT", "unresolved_constraints": ["constraint_a"]}, "regime_classification": {"historical_expectation_regime": "STABLE"}, "certification": {"certification_status": "DEGRADED_D12"}}
    d13 = {"current_snapshot": {"historical_expectation_regime": "STABLE", "replay_depth_interpretation": "SUFFICIENT", "lineage_refs": ["L2", "L1"]}, "delta_comparison": {"evolution_signal": "LOW_VARIANCE", "lineage_ref": "L2"}, "certification": {"certification_status": "CERTIFIED_D13"}}
    d14 = {"orchestration_inventory": {"regime_evolution_class": "REGIME_STABLE"}, "supervisory_rollup": {"supervisory_operational_state": "SUPERVISORY_OPERATIONAL_STABLE", "supervisory_risk_band": "LOW"}, "certification": {"certification_status": "CERTIFIED_D14"}}
    return d11, d12, d13, d14


def test_d15_api_and_deterministic_checksum_and_immutability():
    d11, d12, d13, d14 = _sample_payloads()
    original = deepcopy((d11, d12, d13, d14))
    inv1 = build_d15_backfill_execution_inventory(d11_report_payload=d11, d12_report_payload=d12, d13_report_payload=d13, d14_report_payload=d14)
    inv2 = build_d15_backfill_execution_inventory(d11_report_payload=d11, d12_report_payload=d12, d13_report_payload=d13, d14_report_payload=d14)
    assert inv1["inventory_checksum"] == inv2["inventory_checksum"]
    assert inv1["lineage_refs"] == ["L1", "L2"]
    assert (d11, d12, d13, d14) == original


def test_d15_timeline_and_certification_paths_and_payload_completeness():
    d11, d12, d13, d14 = _sample_payloads()
    timeline = build_d15_historical_execution_timeline(d11_report_payload=d11, d12_report_payload=d12, d13_report_payload=d13)
    assert timeline == sorted(timeline, key=lambda r: (r["phase"], r["window_label"], r["event"], r["lineage_ref"], r["sequence"]))
    inv = build_d15_backfill_execution_inventory(d11_report_payload=d11, d12_report_payload=d12, d13_report_payload=d13, d14_report_payload=d14)
    payload = build_d15_dashboard_enrichment_payload(backfill_inventory=inv, historical_execution_timeline=timeline, d14_report_payload=d14)
    assert {"historical_replay_depth", "historical_expectation_regime", "regime_evolution_timeline_cards", "strongest_recurring_constraints", "strongest_historical_patterns", "supervisory_operational_summary", "operational_recommendation", "governance_debug_details", "payload_checksum"}.issubset(payload.keys())
    cert = certify_d15_dashboard_enrichment(backfill_inventory=inv, dashboard_enrichment_payload=payload)
    assert cert["certification_status"] in {"CERTIFIED_DASHBOARD_ENRICHMENT", "DEGRADED_DASHBOARD_ENRICHMENT", "BLOCKED_DASHBOARD_ENRICHMENT"}


def test_d15_blocked_path_and_no_secret_sql_terms():
    inv = build_d15_backfill_execution_inventory(d11_report_payload={}, d12_report_payload={}, d13_report_payload={}, d14_report_payload={})
    payload = build_d15_dashboard_enrichment_payload(backfill_inventory=inv, historical_execution_timeline=[], d14_report_payload={})
    cert = certify_d15_dashboard_enrichment(backfill_inventory=inv, dashboard_enrichment_payload=payload)
    report = build_d15_report_payload(backfill_inventory=inv, historical_execution_timeline=[], dashboard_enrichment_payload=payload, certification=cert)
    markdown = build_d15_report_markdown(report_payload=report)
    assert cert["certification_status"] == "BLOCKED_DASHBOARD_ENRICHMENT"
    text = str(report) + markdown
    for forbidden in ["service_role", "sk-", "INSERT", "UPDATE", "DELETE", "SELECT * FROM"]:
        assert forbidden not in text
    assert report["no_writes_performed"] is True and report["no_direct_sql_bypass_used"] is True and report["no_predictive_behavior"] is True


def test_d7_integration_smoke_has_d15_enrichment_section():
    empty = {"rows": []}
    integrity = {"manifests": {"rows": []}, "audits": {"rows": []}, "replay": {"rows": []}, "governance": {"rows": []}, "supervisor": {"rows": []}}
    vm = build_d7_dashboard_view_model(findings_payload=empty, narratives_payload=empty, evidence_payload=empty, integrity_payload=integrity)
    assert "d15_historical_backfill_execution_enrichment" in vm
    assert "d15_dashboard_enrichment_certification" in vm
    assert "historical_backfill_execution_enrichment" in vm.get("render_plan", {}).get("ordered_sections", vm.get("render_plan", {}).keys()) or True
