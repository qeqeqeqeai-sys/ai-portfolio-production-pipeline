from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from hashlib import sha256
from typing import Any, Mapping

SEVERITY_ORDER = {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _normalized_findings(d9_report_payload: Mapping[str, Any] | None = None, d9_findings: list[Mapping[str, Any]] | None = None) -> list[dict[str, Any]]:
    src = d9_findings if isinstance(d9_findings, list) else _list(_dict(d9_report_payload).get("operational_findings"))
    findings = [_dict(f) for f in src if isinstance(f, Mapping)]
    return sorted(findings, key=lambda f: (_text(f.get("finding_id")), _text(f.get("category")), _text(f.get("severity"))))


def _checksum(parts: list[str]) -> str:
    return sha256("|".join(parts).encode("utf-8")).hexdigest()[:24].upper()


def build_d10_finding_snapshot(*, d9_report_payload: Mapping[str, Any] | None = None, d9_findings: list[Mapping[str, Any]] | None = None, replay_timestamp: str | None = None, cycle_id: str | None = None) -> OrderedDict[str, Any]:
    findings = _normalized_findings(d9_report_payload=d9_report_payload, d9_findings=d9_findings)
    cert = _dict(d9_report_payload).get("certification") if isinstance(d9_report_payload, Mapping) else {}
    summary = _dict(d9_report_payload).get("expectation_intelligence_summary") if isinstance(d9_report_payload, Mapping) else {}

    fid = [_text(f.get("finding_id")) for f in findings if _text(f.get("finding_id"))]
    categories = sorted({_text(f.get("category")) for f in findings if _text(f.get("category"))})
    sev = OrderedDict()
    for k in ["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        c = sum(1 for f in findings if _text(f.get("severity")).upper() == k)
        if c:
            sev[k] = c
    replay_ids = sorted({x for f in findings for x in _list(f.get("replay_ids")) if _text(x)})
    lineage_refs = sorted({x for f in findings for x in _list(f.get("manifest_checksums")) if _text(x)})
    unresolved = sorted({_text(x) for x in _list(summary.get("unresolved_constraints")) if _text(x)})
    cycle = cycle_id or _text(_dict(d9_report_payload).get("cycle_id")) or _text(replay_timestamp) or "cycle-unknown"

    parts = [cycle, ",".join(fid), ",".join(categories), str(len(fid)), str(dict(sev)), ",".join(unresolved), ",".join(replay_ids), ",".join(lineage_refs)]
    snap_checksum = _checksum(parts)
    snapshot_id = f"D10-SNAPSHOT-{snap_checksum[:12]}"

    return OrderedDict([
        ("snapshot_id", snapshot_id),
        ("cycle_id", cycle),
        ("finding_count", len(findings)),
        ("finding_ids", fid),
        ("categories_present", categories),
        ("severity_distribution", sev),
        ("dominant_operational_state", _text(summary.get("dominant_operational_state")) or "OPERATIONALLY_UNKNOWN"),
        ("unresolved_constraints", unresolved),
        ("replay_ids", replay_ids),
        ("lineage_refs", lineage_refs),
        ("snapshot_checksum", snap_checksum),
        ("d9_certification_status", _text(_dict(cert).get("certification_status"))),
        ("findings", findings),
    ])


def compare_d10_finding_snapshots(*, current_snapshot: Mapping[str, Any], previous_snapshots: list[Mapping[str, Any]] | None = None) -> OrderedDict[str, Any]:
    prev = [_dict(p) for p in _list(previous_snapshots)]
    if not prev:
        return OrderedDict([("new_findings", list(_list(current_snapshot.get("finding_ids")))), ("recurring_findings", []), ("resolved_findings", []), ("severity_changes", []), ("category_changes", []), ("unresolved_constraint_persistence", []), ("monitoring_delta_status", "DELTA_INSUFFICIENT_HISTORY")])
    last = prev[-1]
    cur_ids = set(_list(current_snapshot.get("finding_ids")))
    prev_ids = set(_list(last.get("finding_ids")))
    new_ids = sorted(cur_ids - prev_ids)
    recur = sorted(cur_ids & prev_ids)
    resolved = sorted(prev_ids - cur_ids)
    cur_by = {_text(f.get("finding_id")): _dict(f) for f in _list(current_snapshot.get("findings")) if _text(_dict(f).get("finding_id"))}
    prev_by = {_text(f.get("finding_id")): _dict(f) for f in _list(last.get("findings")) if _text(_dict(f).get("finding_id"))}
    sev_changes = []
    cat_changes = []
    for fid in sorted(cur_ids & prev_ids):
        csev = _text(cur_by.get(fid, {}).get("severity")).upper()
        psev = _text(prev_by.get(fid, {}).get("severity")).upper()
        if csev != psev:
            sev_changes.append(OrderedDict([("finding_id", fid), ("previous", psev), ("current", csev)]))
        ccat = _text(cur_by.get(fid, {}).get("category"))
        pcat = _text(prev_by.get(fid, {}).get("category"))
        if ccat != pcat:
            cat_changes.append(OrderedDict([("finding_id", fid), ("previous", pcat), ("current", ccat)]))
    unresolved_persist = sorted(set(_list(current_snapshot.get("unresolved_constraints"))) & set(_list(last.get("unresolved_constraints"))))
    changed = bool(new_ids or resolved or sev_changes or cat_changes)
    return OrderedDict([("new_findings", new_ids), ("recurring_findings", recur), ("resolved_findings", resolved), ("severity_changes", sev_changes), ("category_changes", cat_changes), ("unresolved_constraint_persistence", unresolved_persist), ("monitoring_delta_status", "DELTA_CHANGED" if changed else "DELTA_STABLE")])


def classify_d10_finding_persistence(*, current_snapshot: Mapping[str, Any], previous_snapshots: list[Mapping[str, Any]] | None = None) -> list[OrderedDict[str, Any]]:
    prev = _dict(_list(previous_snapshots)[-1]) if _list(previous_snapshots) else {}
    prev_by = {_text(f.get("finding_id")): _dict(f) for f in _list(prev.get("findings")) if _text(_dict(f).get("finding_id"))}
    out = []
    for f in _list(current_snapshot.get("findings")):
        ff = _dict(f)
        fid = _text(ff.get("finding_id"))
        cur_sev = _text(ff.get("severity")).upper()
        p = prev_by.get(fid)
        if not p:
            cls = "NEW_FINDING"
        else:
            prev_sev = _text(p.get("severity")).upper()
            if SEVERITY_ORDER.get(cur_sev, -1) > SEVERITY_ORDER.get(prev_sev, -1):
                cls = "ESCALATING_FINDING"
            elif SEVERITY_ORDER.get(cur_sev, -1) < SEVERITY_ORDER.get(prev_sev, -1):
                cls = "DEESCALATING_FINDING"
            elif cur_sev == prev_sev:
                cls = "STABLE_FINDING"
            else:
                cls = "RECURRING_FINDING"
        out.append(OrderedDict([("finding_id", fid), ("persistence_class", cls), ("severity", cur_sev), ("category", _text(ff.get("category")))]))
    return sorted(out, key=lambda x: x["finding_id"])


def evaluate_d10_alert_readiness(*, current_snapshot: Mapping[str, Any], delta_comparison: Mapping[str, Any], persistence_classification: list[Mapping[str, Any]]) -> OrderedDict[str, Any]:
    d9_ok = _text(current_snapshot.get("d9_certification_status")) == "CERTIFIED_FINDING_GENERATION"
    has_findings = int(current_snapshot.get("finding_count") or 0) > 0
    has_trace = bool(_list(current_snapshot.get("replay_ids"))) and bool(_list(current_snapshot.get("lineage_refs")))
    recurring_constraints = bool(_list(delta_comparison.get("unresolved_constraint_persistence")))
    escalating = any(_text(x.get("persistence_class")) == "ESCALATING_FINDING" for x in _list(persistence_classification))
    new_high = any(_text(x.get("persistence_class")) == "NEW_FINDING" and SEVERITY_ORDER.get(_text(x.get("severity")).upper(), -1) >= SEVERITY_ORDER["HIGH"] for x in _list(persistence_classification))
    sufficient_history = _text(delta_comparison.get("monitoring_delta_status")) != "DELTA_INSUFFICIENT_HISTORY"
    if not d9_ok or not has_findings or not has_trace:
        status = "ALERT_BLOCKED"
    elif recurring_constraints or escalating or new_high:
        status = "ALERT_READY" if (sufficient_history or new_high) else "ALERT_DEGRADED"
    else:
        status = "ALERT_DEGRADED"
    return OrderedDict([("alert_readiness_status", status), ("d9_certified", d9_ok), ("sufficient_history", sufficient_history), ("drivers", OrderedDict([("recurring_unresolved_constraints", recurring_constraints), ("escalating_findings", escalating), ("new_high_severity_finding", new_high)])), ("alerts_sent", False)])


def build_d10_monitoring_cards(*, current_snapshot: Mapping[str, Any], delta_comparison: Mapping[str, Any], persistence_classification: list[Mapping[str, Any]], alert_readiness: Mapping[str, Any]) -> OrderedDict[str, Any]:
    escalating_count = sum(1 for x in _list(persistence_classification) if _text(x.get("persistence_class")) == "ESCALATING_FINDING")
    status = _text(delta_comparison.get("monitoring_delta_status"))
    rec = "Proceed to governed alerting dry-run design (no live delivery)." if _text(alert_readiness.get("alert_readiness_status")) in {"ALERT_READY", "ALERT_DEGRADED"} else "Resolve certification/traceability blockers before alerting readiness."
    return OrderedDict([
        ("monitoring_status", status), ("finding_count", int(current_snapshot.get("finding_count") or 0)),
        ("new_finding_count", len(_list(delta_comparison.get("new_findings")))), ("recurring_finding_count", len(_list(delta_comparison.get("recurring_findings")))),
        ("resolved_finding_count", len(_list(delta_comparison.get("resolved_findings")))), ("escalating_finding_count", escalating_count),
        ("dominant_operational_state", current_snapshot.get("dominant_operational_state")),
        ("unresolved_constraint_persistence", _list(delta_comparison.get("unresolved_constraint_persistence"))),
        ("alert_readiness_status", alert_readiness.get("alert_readiness_status")), ("recommendation", rec),
    ])


def certify_d10_monitoring_readiness(*, current_snapshot: Mapping[str, Any], delta_comparison: Mapping[str, Any], monitoring_cards: Mapping[str, Any], alert_readiness: Mapping[str, Any]) -> OrderedDict[str, Any]:
    d9_ok = _text(current_snapshot.get("d9_certification_status")) == "CERTIFIED_FINDING_GENERATION"
    has_findings = int(current_snapshot.get("finding_count") or 0) > 0
    has_trace = bool(_list(current_snapshot.get("replay_ids"))) and bool(_list(current_snapshot.get("lineage_refs")))
    cards_ok = all(k in monitoring_cards for k in ["monitoring_status", "finding_count", "new_finding_count", "recurring_finding_count", "resolved_finding_count", "escalating_finding_count", "dominant_operational_state", "unresolved_constraint_persistence", "alert_readiness_status", "recommendation"])
    delta_ok = _text(delta_comparison.get("monitoring_delta_status")) in {"DELTA_STABLE", "DELTA_CHANGED", "DELTA_INSUFFICIENT_HISTORY"}
    alert_status = _text(alert_readiness.get("alert_readiness_status"))
    if not d9_ok or not has_findings or not has_trace:
        status = "BLOCKED_MONITORING"
    elif delta_ok and cards_ok and alert_status in {"ALERT_READY", "ALERT_DEGRADED"}:
        status = "CERTIFIED_MONITORING_READY" if alert_status == "ALERT_READY" else "DEGRADED_MONITORING_READY"
    else:
        status = "DEGRADED_MONITORING_READY"
    return OrderedDict([("certification_status", status), ("d9_certified", d9_ok), ("delta_valid", delta_ok), ("cards_complete", cards_ok)])


def build_d10_report_payload(*, objective: str = "D10 Longitudinal Finding Monitoring & Alerting Readiness", current_snapshot: Mapping[str, Any], delta_comparison: Mapping[str, Any], persistence_classification: list[Mapping[str, Any]], monitoring_cards: Mapping[str, Any], alert_readiness: Mapping[str, Any], certification: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([("objective", objective), ("current_snapshot", OrderedDict(deepcopy(dict(current_snapshot)))), ("delta_comparison", OrderedDict(deepcopy(dict(delta_comparison)))), ("persistence_classification", [OrderedDict(deepcopy(dict(x))) for x in _list(persistence_classification)]), ("monitoring_cards", OrderedDict(deepcopy(dict(monitoring_cards)))), ("alert_readiness", OrderedDict(deepcopy(dict(alert_readiness)))), ("certification", OrderedDict(deepcopy(dict(certification)))), ("no_direct_sql_bypass_used", True), ("no_alerts_sent", True), ("no_writes_performed", True), ("recommendation", monitoring_cards.get("recommendation") or certification.get("certification_status"))])


def build_d10_report_markdown(*, report_payload: Mapping[str, Any]) -> str:
    snap = _dict(report_payload.get("current_snapshot")); delta = _dict(report_payload.get("delta_comparison")); cards = _dict(report_payload.get("monitoring_cards")); alert = _dict(report_payload.get("alert_readiness")); cert = _dict(report_payload.get("certification"))
    return "\n".join([
        "# D10 Longitudinal Finding Monitoring & Alerting Readiness", "", f"## Objective\n- {report_payload.get('objective')}", "## Scope\n- Deterministic longitudinal monitoring of D9 findings across replay cycles.", "## Non-goals\n- No writes.\n- No direct SQL.\n- No live alert delivery.\n- No predictive/trading signals.",
        f"## Current Finding Snapshot\n- Snapshot ID: {snap.get('snapshot_id')}\n- Cycle ID: {snap.get('cycle_id')}\n- Finding count: {snap.get('finding_count')}",
        f"## Longitudinal Delta Comparison\n- Status: {delta.get('monitoring_delta_status')}\n- New: {len(_list(delta.get('new_findings')))}\n- Recurring: {len(_list(delta.get('recurring_findings')))}\n- Resolved: {len(_list(delta.get('resolved_findings')))}",
        f"## Persistence Classification\n- Classified findings: {len(_list(report_payload.get('persistence_classification')))}",
        f"## Monitoring Cards\n- Monitoring status: {cards.get('monitoring_status')}\n- Alert readiness: {cards.get('alert_readiness_status')}\n- Recommendation: {cards.get('recommendation')}",
        f"## Alert Readiness Evaluation\n- Status: {alert.get('alert_readiness_status')}\n- Drivers: {alert.get('drivers')}",
        f"## Certification\n- {cert.get('certification_status')}",
        "## Governance Boundaries\n- no_direct_sql_bypass_used: True\n- no_alerts_sent: True\n- no_writes_performed: True\n- Deterministic ordering and replay traceability preserved.",
        f"## Final Recommendation\n- {report_payload.get('recommendation')}",
    ])
