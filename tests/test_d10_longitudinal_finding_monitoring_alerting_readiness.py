from copy import deepcopy

from transmission_layers.expectation_failure.expectation_intelligence import (
    build_d10_finding_snapshot,
    compare_d10_finding_snapshots,
    classify_d10_finding_persistence,
    build_d10_monitoring_cards,
    evaluate_d10_alert_readiness,
    certify_d10_monitoring_readiness,
    build_d10_report_payload,
    build_d10_report_markdown,
)


def _d9_payload(cert="CERTIFIED_FINDING_GENERATION", findings=None, unresolved=None):
    return {
        "certification": {"certification_status": cert},
        "expectation_intelligence_summary": {"dominant_operational_state": "OPERATIONALLY_READY", "unresolved_constraints": unresolved or []},
        "operational_findings": findings or [],
    }


def _finding(fid, sev="INFO", cat="c1"):
    return {"finding_id": fid, "severity": sev, "category": cat, "replay_ids": ["R1"], "manifest_checksums": ["M1"]}


def test_api_export_presence():
    assert callable(build_d10_finding_snapshot)


def test_snapshot_checksum_deterministic_and_input_immutable():
    p = _d9_payload(findings=[_finding("F2"), _finding("F1")], unresolved=["x"])
    c = deepcopy(p)
    s1 = build_d10_finding_snapshot(d9_report_payload=p, cycle_id="c1")
    s2 = build_d10_finding_snapshot(d9_report_payload=p, cycle_id="c1")
    assert s1["snapshot_checksum"] == s2["snapshot_checksum"]
    assert p == c


def test_delta_insufficient_history_and_new_recurring_resolved():
    cur = build_d10_finding_snapshot(d9_report_payload=_d9_payload(findings=[_finding("F1"), _finding("F2")]))
    delta0 = compare_d10_finding_snapshots(current_snapshot=cur, previous_snapshots=[])
    assert delta0["monitoring_delta_status"] == "DELTA_INSUFFICIENT_HISTORY"
    prev = build_d10_finding_snapshot(d9_report_payload=_d9_payload(findings=[_finding("F1"), _finding("F3")]))
    delta = compare_d10_finding_snapshots(current_snapshot=cur, previous_snapshots=[prev])
    assert "F2" in delta["new_findings"] and "F1" in delta["recurring_findings"] and "F3" in delta["resolved_findings"]


def test_severity_escalation_deescalation_and_unresolved_persistence():
    prev = build_d10_finding_snapshot(d9_report_payload=_d9_payload(findings=[_finding("F1", "LOW"), _finding("F2", "HIGH")], unresolved=["u1", "u2"]))
    cur = build_d10_finding_snapshot(d9_report_payload=_d9_payload(findings=[_finding("F1", "HIGH"), _finding("F2", "MEDIUM")], unresolved=["u1"]))
    delta = compare_d10_finding_snapshots(current_snapshot=cur, previous_snapshots=[prev])
    cls = classify_d10_finding_persistence(current_snapshot=cur, previous_snapshots=[prev])
    by = {x["finding_id"]: x["persistence_class"] for x in cls}
    assert by["F1"] == "ESCALATING_FINDING" and by["F2"] == "DEESCALATING_FINDING"
    assert delta["unresolved_constraint_persistence"] == ["u1"]


def test_alert_readiness_and_certification_paths_and_cards_and_reports():
    blocked_snapshot = build_d10_finding_snapshot(d9_report_payload=_d9_payload(cert="BLOCKED_FINDING_GENERATION", findings=[_finding("F1", "HIGH")]))
    delta = compare_d10_finding_snapshots(current_snapshot=blocked_snapshot, previous_snapshots=[])
    cls = classify_d10_finding_persistence(current_snapshot=blocked_snapshot, previous_snapshots=[])
    blocked_alert = evaluate_d10_alert_readiness(current_snapshot=blocked_snapshot, delta_comparison=delta, persistence_classification=cls)
    assert blocked_alert["alert_readiness_status"] == "ALERT_BLOCKED"

    prev = build_d10_finding_snapshot(d9_report_payload=_d9_payload(findings=[_finding("F1", "LOW")], unresolved=["u1"]))
    cur = build_d10_finding_snapshot(d9_report_payload=_d9_payload(findings=[_finding("F1", "HIGH")], unresolved=["u1"]))
    delta2 = compare_d10_finding_snapshots(current_snapshot=cur, previous_snapshots=[prev])
    cls2 = classify_d10_finding_persistence(current_snapshot=cur, previous_snapshots=[prev])
    alert = evaluate_d10_alert_readiness(current_snapshot=cur, delta_comparison=delta2, persistence_classification=cls2)
    assert alert["alert_readiness_status"] == "ALERT_READY"
    cards = build_d10_monitoring_cards(current_snapshot=cur, delta_comparison=delta2, persistence_classification=cls2, alert_readiness=alert)
    required = {"monitoring_status", "finding_count", "new_finding_count", "recurring_finding_count", "resolved_finding_count", "escalating_finding_count", "dominant_operational_state", "unresolved_constraint_persistence", "alert_readiness_status", "recommendation"}
    assert required.issubset(cards.keys())
    cert = certify_d10_monitoring_readiness(current_snapshot=cur, delta_comparison=delta2, monitoring_cards=cards, alert_readiness=alert)
    assert cert["certification_status"] == "CERTIFIED_MONITORING_READY"
    deg_cert = certify_d10_monitoring_readiness(current_snapshot=cur, delta_comparison=delta2, monitoring_cards=cards, alert_readiness={"alert_readiness_status": "ALERT_DEGRADED"})
    assert deg_cert["certification_status"] == "DEGRADED_MONITORING_READY"
    blk_cert = certify_d10_monitoring_readiness(current_snapshot=blocked_snapshot, delta_comparison=delta, monitoring_cards=cards, alert_readiness=blocked_alert)
    assert blk_cert["certification_status"] == "BLOCKED_MONITORING"

    payload = build_d10_report_payload(current_snapshot=cur, delta_comparison=delta2, persistence_classification=cls2, monitoring_cards=cards, alert_readiness=alert, certification=cert)
    assert payload["no_alerts_sent"] is True and payload["no_writes_performed"] is True and payload["no_direct_sql_bypass_used"] is True
    assert "secret" not in str(payload).lower()
    md = build_d10_report_markdown(report_payload=payload)
    for section in ["Objective", "Scope", "Non-goals", "Current Finding Snapshot", "Longitudinal Delta Comparison", "Persistence Classification", "Monitoring Cards", "Alert Readiness Evaluation", "Certification", "Governance Boundaries", "Final Recommendation"]:
        assert f"## {section}" in md
