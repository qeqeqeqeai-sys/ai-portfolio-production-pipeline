from copy import deepcopy

from transmission_layers.expectation_failure.expectation_intelligence.d17_historical_confidence_attribution_lineage_compression import (
    build_d17_confidence_attribution_inventory,
    build_d17_constraint_weight_summary,
    build_d17_lineage_trace_compression,
    build_d17_historical_confidence_overlays,
    build_d17_operator_drilldown_payload,
    build_d17_dashboard_payload,
    certify_d17_confidence_lineage_enrichment,
    build_d17_report_payload,
    build_d17_report_markdown,
)


def _sample_d16():
    return {
        "recurring_historical_findings": [{"cluster_id": "D16_CLUSTER_001", "finding": "VOL_SPIKE"}],
        "recurrent_confidence_constraints": ["SPARSE_EVIDENCE", "CONTINUITY_DEGRADED"],
        "what_changed": ["REGIME_SHIFT_A"],
        "governance_lineage_details": {"lineage_refs": ["L1", "L2"]},
    }


def test_d17_api_determinism_checksum_and_input_immutable():
    d16 = _sample_d16(); d15 = {"historical_replay_depth": "SUFFICIENT", "historical_continuity_status": "CONTINUOUS"}
    d12 = {"expectation_intelligence_synthesis": {"unresolved_constraints": ["SPARSE_EVIDENCE"]}}
    d13 = {"delta_comparison": {"evolution_signal": "STABLE"}}
    frozen = deepcopy(d16)
    inv = build_d17_confidence_attribution_inventory(d16_dashboard_payload=d16, d15_dashboard_enrichment_payload=d15, d12_report_payload=d12, d13_report_payload=d13)
    csum = build_d17_constraint_weight_summary(confidence_attribution_inventory=inv, d12_report_payload=d12)
    lin1 = build_d17_lineage_trace_compression(d16_dashboard_payload=d16, d11_report_payload={"historical_replay_windows": {"lineage_refs": ["L3"]}}, d14_report_payload={"supervisory_rollup": {"supervisory_risk_band": "MODERATE"}})
    lin2 = build_d17_lineage_trace_compression(d16_dashboard_payload=d16, d11_report_payload={"historical_replay_windows": {"lineage_refs": ["L3"]}}, d14_report_payload={"supervisory_rollup": {"supervisory_risk_band": "MODERATE"}})
    assert lin1 == lin2
    ov = build_d17_historical_confidence_overlays(confidence_attribution_inventory=inv, constraint_weight_summary=csum, lineage_trace_compression=lin1)
    dd = build_d17_operator_drilldown_payload(confidence_attribution_inventory=inv, lineage_trace_compression=lin1, d16_dashboard_payload=d16)
    dash = build_d17_dashboard_payload(confidence_attribution_inventory=inv, constraint_weight_summary=csum, lineage_trace_compression=lin1, historical_confidence_overlays=ov, operator_drilldown_payload=dd)
    cert = certify_d17_confidence_lineage_enrichment(d16_dashboard_payload=d16, historical_confidence_overlays=ov, lineage_trace_compression=lin1, dashboard_payload=dash)
    report = build_d17_report_payload(confidence_attribution_inventory=inv, constraint_weight_summary=csum, lineage_trace_compression=lin1, historical_confidence_overlays=ov, operator_drilldown_payload=dd, dashboard_payload=dash, certification=cert)
    md = build_d17_report_markdown(report_payload=report)
    assert d16 == frozen
    assert cert["certification_status"].startswith("CERTIFIED")
    assert "No direct SQL" in md


def test_d17_degraded_blocked_and_guardrails():
    cert_blocked = certify_d17_confidence_lineage_enrichment(d16_dashboard_payload={"recurring_historical_findings": []}, historical_confidence_overlays={}, lineage_trace_compression={}, dashboard_payload={"text": "buy now"})
    assert cert_blocked["certification_status"].startswith("BLOCKED")
    assert "FORBIDDEN_PREDICTIVE_TRADING_OR_AUTONOMOUS_LANGUAGE" in cert_blocked["blocking_reasons"]
    inv = build_d17_confidence_attribution_inventory(d16_dashboard_payload=_sample_d16(), d15_dashboard_enrichment_payload={}, d12_report_payload={}, d13_report_payload={})
    assert inv[0]["confidence_band"] in {"high", "moderate", "low", "degraded", "unavailable"}
    dd = build_d17_operator_drilldown_payload(confidence_attribution_inventory=inv, lineage_trace_compression={"compressed_replay_references": ["RPL:ABC"]}, d16_dashboard_payload=_sample_d16())
    assert "recurring_findings" in dd and "degraded_findings" in dd
