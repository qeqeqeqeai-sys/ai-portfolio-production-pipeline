from copy import deepcopy

from transmission_layers.expectation_failure.expectation_intelligence.d16_historical_findings_replay_operator_narrative import (
    BLOCKED_HISTORICAL_FINDINGS_NARRATIVE,
    CERTIFIED_HISTORICAL_FINDINGS_NARRATIVE,
    DEGRADED_HISTORICAL_FINDINGS_NARRATIVE,
    build_d16_dashboard_payload,
    build_d16_historical_finding_inventory,
    build_d16_operator_narrative_summary,
    build_d16_recurring_finding_clusters,
    build_d16_regime_linked_finding_narratives,
    build_d16_report_markdown,
    build_d16_report_payload,
    certify_d16_historical_findings_narrative,
)


def _fixtures():
    d11 = {"historical_replay_windows": {"lineage_refs": ["L1", "L2"]}}
    d12 = {"cross_window_patterns": [{"pattern_classification": "CONSTRAINT_A"}], "expectation_intelligence_synthesis": {"unresolved_constraints": ["LOW_SIGNAL"], "cross_window_pattern_summary": ["CONSTRAINT_A"]}, "historical_expectation_inventory": {"lineage_refs": ["L3"]}, "regime_classification": {"historical_expectation_regime": "REGIME_STABLE"}}
    d13 = {"current_snapshot": {"historical_expectation_regime": "REGIME_STABLE", "lineage_refs": ["L4"]}, "delta_comparison": {"evolution_signal": "REGIME_EVOLVING"}}
    d14 = {"orchestration_inventory": {"regime_evolution_class": "REGIME_EVOLVING"}}
    d15 = {"historical_replay_depth": "SUFFICIENT", "historical_expectation_regime": "REGIME_STABLE", "strongest_historical_patterns": ["PATTERN_A"], "governance_debug_details": {"lineage_refs": ["L5"]}}
    return d11, d12, d13, d14, d15


def test_d16_api_and_determinism_and_checksum():
    d11, d12, d13, d14, d15 = _fixtures()
    inv = build_d16_historical_finding_inventory(d11_report_payload=d11, d12_report_payload=d12, d13_report_payload=d13, d14_report_payload=d14, d15_dashboard_enrichment_payload=d15)
    clusters = build_d16_recurring_finding_clusters(historical_finding_inventory=inv, d12_report_payload=d12)
    narratives = build_d16_regime_linked_finding_narratives(recurring_finding_clusters=clusters, d13_report_payload=d13, d14_report_payload=d14)
    summary = build_d16_operator_narrative_summary(historical_finding_inventory=inv, recurring_finding_clusters=clusters, regime_linked_finding_narratives=narratives, d15_dashboard_enrichment_payload=d15)
    payload1 = build_d16_dashboard_payload(historical_finding_inventory=inv, recurring_finding_clusters=clusters, regime_linked_finding_narratives=narratives, operator_narrative_summary=summary)
    payload2 = build_d16_dashboard_payload(historical_finding_inventory=inv, recurring_finding_clusters=clusters, regime_linked_finding_narratives=narratives, operator_narrative_summary=summary)
    assert payload1 == payload2
    assert payload1["payload_checksum"] == payload2["payload_checksum"]
    assert list(payload1.keys())[0] == "recurring_historical_findings"


def test_d16_input_immutable_and_certification_paths():
    d11, d12, d13, d14, d15 = _fixtures()
    original = deepcopy((d11, d12, d13, d14, d15))
    inv = build_d16_historical_finding_inventory(d11_report_payload=d11, d12_report_payload=d12, d13_report_payload=d13, d14_report_payload=d14, d15_dashboard_enrichment_payload=d15)
    clusters = build_d16_recurring_finding_clusters(historical_finding_inventory=inv, d12_report_payload=d12)
    narratives = build_d16_regime_linked_finding_narratives(recurring_finding_clusters=clusters, d13_report_payload=d13, d14_report_payload=d14)
    summary = build_d16_operator_narrative_summary(historical_finding_inventory=inv, recurring_finding_clusters=clusters, regime_linked_finding_narratives=narratives, d15_dashboard_enrichment_payload=d15)
    payload = build_d16_dashboard_payload(historical_finding_inventory=inv, recurring_finding_clusters=clusters, regime_linked_finding_narratives=narratives, operator_narrative_summary=summary)
    cert = certify_d16_historical_findings_narrative(historical_finding_inventory=inv, recurring_finding_clusters=clusters, regime_linked_finding_narratives=narratives, operator_narrative_summary=summary, dashboard_payload=payload)
    assert cert["certification_status"] == CERTIFIED_HISTORICAL_FINDINGS_NARRATIVE
    assert (d11, d12, d13, d14, d15) == original

    blocked = certify_d16_historical_findings_narrative(historical_finding_inventory={"lineage_refs": [], "recurring_historical_findings": []}, recurring_finding_clusters=[], regime_linked_finding_narratives=[], operator_narrative_summary={}, dashboard_payload={"text": "buy now"})
    assert blocked["certification_status"] == BLOCKED_HISTORICAL_FINDINGS_NARRATIVE

    degraded = certify_d16_historical_findings_narrative(historical_finding_inventory={"lineage_refs": ["L1"], "recurring_historical_findings": ["X"]}, recurring_finding_clusters=[], regime_linked_finding_narratives=[], operator_narrative_summary={"summary_narrative": "ok"}, dashboard_payload={})
    assert degraded["certification_status"] == DEGRADED_HISTORICAL_FINDINGS_NARRATIVE


def test_d16_report_payload_and_markdown_flags():
    report = build_d16_report_payload(historical_finding_inventory={"lineage_refs": ["L1"]}, recurring_finding_clusters=[], regime_linked_finding_narratives=[], operator_narrative_summary={"summary_narrative": "ok"}, dashboard_payload={}, certification={"certification_status": "X"})
    md = build_d16_report_markdown(report_payload=report)
    assert report["no_writes_performed"] is True
    assert report["no_direct_sql_bypass_used"] is True
    assert report["no_predictive_behavior"] is True
    assert "No direct SQL" in md
