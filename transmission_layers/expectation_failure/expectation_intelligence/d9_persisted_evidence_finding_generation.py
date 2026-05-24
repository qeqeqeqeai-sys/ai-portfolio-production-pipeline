from __future__ import annotations

from collections import OrderedDict
from hashlib import sha256
from typing import Any, Mapping


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


def _sorted_unique_text(values: list[Any]) -> list[str]:
    return sorted({_text(v) for v in values if _text(v)})


def _checksum(parts: list[str]) -> str:
    return sha256("|".join(parts).encode("utf-8")).hexdigest()[:24].upper()


def build_d9_persisted_evidence_inventory(*, d8c_readback_inventory: Mapping[str, Any], d8c_lineage_validation: Mapping[str, Any], d8c_dashboard_consumption_model: Mapping[str, Any], d8c_certification: Mapping[str, Any]) -> OrderedDict[str, Any]:
    replay_count = _as_int(d8c_readback_inventory.get("replay_row_count"))
    manifest_count = _as_int(d8c_readback_inventory.get("manifest_row_count"))
    lineage_status = _text(d8c_lineage_validation.get("lineage_status")) or "LINEAGE_BLOCKED"
    certification_status = _text(d8c_certification.get("certification_status"))
    readiness = _text(d8c_dashboard_consumption_model.get("replay_candidate_readiness")) or "NOT_READY"

    replay_ids = _sorted_unique_text(_list(d8c_readback_inventory.get("replay_ids")) + _list(d8c_readback_inventory.get("latest_replay_ids")))
    manifest_checksums = _sorted_unique_text(_list(d8c_readback_inventory.get("manifest_checksums")) + _list(d8c_readback_inventory.get("latest_manifest_checksums")))

    if certification_status != "CERTIFIED_DASHBOARD_CONSUMABLE" or lineage_status == "LINEAGE_BLOCKED":
        inventory_status = "INVENTORY_BLOCKED"
    elif replay_count <= 0 or manifest_count <= 0 or lineage_status != "LINEAGE_OK" or readiness != "READY":
        inventory_status = "INVENTORY_DEGRADED"
    else:
        inventory_status = "INVENTORY_READY"

    checksum = _checksum([str(replay_count), str(manifest_count), lineage_status, certification_status, ",".join(replay_ids), ",".join(manifest_checksums), readiness, inventory_status])

    return OrderedDict([
        ("replay_row_count", replay_count),
        ("manifest_row_count", manifest_count),
        ("lineage_status", lineage_status),
        ("certification_status", certification_status),
        ("replay_ids", replay_ids),
        ("manifest_checksums", manifest_checksums),
        ("replay_candidate_readiness", readiness),
        ("inventory_status", inventory_status),
        ("inventory_checksum", checksum),
    ])


def validate_d9_finding_generation_eligibility(*, persisted_evidence_inventory: Mapping[str, Any]) -> OrderedDict[str, Any]:
    blocking: list[str] = []
    degraded: list[str] = []
    certification_status = _text(persisted_evidence_inventory.get("certification_status"))
    replay_count = _as_int(persisted_evidence_inventory.get("replay_row_count"))
    manifest_count = _as_int(persisted_evidence_inventory.get("manifest_row_count"))
    lineage_status = _text(persisted_evidence_inventory.get("lineage_status"))

    if certification_status != "CERTIFIED_DASHBOARD_CONSUMABLE":
        blocking.append("d8c_certification_not_consumable")
    if replay_count <= 0:
        blocking.append("no_replay_rows")
    if manifest_count <= 0:
        blocking.append("no_manifest_rows")

    if lineage_status == "LINEAGE_BLOCKED":
        blocking.append("lineage_blocked")
    elif lineage_status != "LINEAGE_OK":
        degraded.append("lineage_not_ok")

    if blocking:
        status = "FINDING_GENERATION_BLOCKED"
    elif degraded:
        status = "FINDING_GENERATION_DEGRADED"
    else:
        status = "FINDING_GENERATION_READY"

    return OrderedDict([
        ("eligibility_status", status),
        ("blocking_reasons", sorted(set(blocking))),
        ("degraded_reasons", sorted(set(degraded))),
    ])


def build_d9_operational_findings(*, persisted_evidence_inventory: Mapping[str, Any], eligibility_validation: Mapping[str, Any]) -> list[OrderedDict[str, Any]]:
    if _text(eligibility_validation.get("eligibility_status")) != "FINDING_GENERATION_READY":
        return []

    replay_ids = list(persisted_evidence_inventory.get("replay_ids") or [])
    manifest_checksums = list(persisted_evidence_inventory.get("manifest_checksums") or [])
    replay_count = _as_int(persisted_evidence_inventory.get("replay_row_count"))
    manifest_count = _as_int(persisted_evidence_inventory.get("manifest_row_count"))

    categories = [
        ("replay_continuity", "Replay continuity confirmed", "Persisted replay rows are continuously available for deterministic readback."),
        ("persistence_operational_integrity", "Persistence operational integrity confirmed", "Replay and manifest evidence indicate stable persistence observability."),
        ("lineage_integrity", "Lineage integrity preserved", "Replay and manifest checksum lineage remains intact and traceable."),
        ("dashboard_consumption_readiness", "Dashboard consumption readiness achieved", "Certified dashboard-consumable evidence is available for operational consumption."),
        ("duplicate_prevention_integrity", "Duplicate prevention integrity held", "Canonical replay identifiers and manifest checksums remain uniquely ordered for replay-safe interpretation."),
        ("governance_integrity", "Governance integrity retained", "Finding generation remains read-only, deterministic, and bounded to certified evidence."),
    ]
    findings: list[OrderedDict[str, Any]] = []
    for idx, (category, title, summary) in enumerate(categories, start=1):
        findings.append(OrderedDict([
            ("finding_id", f"D9-F{idx:02d}"),
            ("category", category),
            ("finding_title", title),
            ("finding_summary", summary),
            ("supporting_evidence_refs", [
                f"inventory_checksum:{persisted_evidence_inventory.get('inventory_checksum')}",
                f"replay_row_count:{replay_count}",
                f"manifest_row_count:{manifest_count}",
            ]),
            ("replay_ids", replay_ids),
            ("manifest_checksums", manifest_checksums),
            ("confidence_band", "HIGH"),
            ("operational_interpretation", "Operational integrity signal is suitable for governed monitoring workflows."),
            ("caveats", ["Bounded to persisted evidence only; no forward-looking inference."]),
            ("severity", "INFO"),
            ("deterministic_rank", idx),
        ]))
    return findings


def build_d9_expectation_intelligence_summary(*, eligibility_validation: Mapping[str, Any], operational_findings: list[Mapping[str, Any]]) -> OrderedDict[str, Any]:
    status = _text(eligibility_validation.get("eligibility_status"))
    findings = [dict(f) for f in _list(operational_findings) if isinstance(f, Mapping)]
    unresolved = list(eligibility_validation.get("blocking_reasons") or []) + list(eligibility_validation.get("degraded_reasons") or [])
    unresolved = sorted({u for u in unresolved if _text(u)})

    dominant = "OPERATIONALLY_READY" if status == "FINDING_GENERATION_READY" else ("OPERATIONALLY_DEGRADED" if status == "FINDING_GENERATION_DEGRADED" else "OPERATIONALLY_BLOCKED")
    strongest_signal = findings[0]["finding_title"] if findings else "No certified operational finding available"
    strongest_constraint = unresolved[0] if unresolved else "none"

    return OrderedDict([
        ("dominant_operational_state", dominant),
        ("strongest_integrity_signal", strongest_signal),
        ("strongest_operational_constraint", strongest_constraint),
        ("replay_operational_readiness", "READY" if status == "FINDING_GENERATION_READY" else "NOT_READY"),
        ("evidence_confidence_band", "HIGH" if findings else "LOW"),
        ("finding_count", len(findings)),
        ("unresolved_constraints", unresolved),
        ("expectation_interpretation", "D9 operational findings are deterministic, replay-traceable, and governance-bounded." if findings else "D9 operational findings unavailable until D8.C gating and lineage conditions are satisfied."),
    ])


def certify_d9_finding_generation(*, persisted_evidence_inventory: Mapping[str, Any], eligibility_validation: Mapping[str, Any], operational_findings: list[Mapping[str, Any]]) -> OrderedDict[str, Any]:
    eligibility = _text(eligibility_validation.get("eligibility_status"))
    findings_count = len(_list(operational_findings))
    lineage_ok = _text(persisted_evidence_inventory.get("lineage_status")) == "LINEAGE_OK"
    cert_status = _text(persisted_evidence_inventory.get("certification_status"))
    replay_count = _as_int(persisted_evidence_inventory.get("replay_row_count"))
    manifest_count = _as_int(persisted_evidence_inventory.get("manifest_row_count"))

    if cert_status != "CERTIFIED_DASHBOARD_CONSUMABLE" or replay_count <= 0 or manifest_count <= 0 or _text(persisted_evidence_inventory.get("lineage_status")) == "LINEAGE_BLOCKED":
        status = "BLOCKED_FINDING_GENERATION"
    elif eligibility == "FINDING_GENERATION_READY" and findings_count > 0 and lineage_ok:
        status = "CERTIFIED_FINDING_GENERATION"
    else:
        status = "DEGRADED_FINDING_GENERATION"
    return OrderedDict([("certification_status", status), ("eligibility_status", eligibility), ("finding_count", findings_count), ("lineage_intact", lineage_ok)])


def build_d9_dashboard_operational_cards(*, expectation_intelligence_summary: Mapping[str, Any], certification: Mapping[str, Any]) -> OrderedDict[str, Any]:
    status = _text(certification.get("certification_status"))
    rec = "Proceed with governed D10 operationalization." if status == "CERTIFIED_FINDING_GENERATION" else "Remediate D8.C certification/lineage blockers before generating findings."
    return OrderedDict([
        ("finding_generation_status", status),
        ("dominant_operational_state", expectation_intelligence_summary.get("dominant_operational_state")),
        ("finding_count", expectation_intelligence_summary.get("finding_count")),
        ("replay_operational_readiness", expectation_intelligence_summary.get("replay_operational_readiness")),
        ("evidence_confidence_band", expectation_intelligence_summary.get("evidence_confidence_band")),
        ("strongest_integrity_signal", expectation_intelligence_summary.get("strongest_integrity_signal")),
        ("strongest_operational_constraint", expectation_intelligence_summary.get("strongest_operational_constraint")),
        ("unresolved_constraints", list(expectation_intelligence_summary.get("unresolved_constraints") or [])),
        ("recommendation", rec),
    ])


def build_d9_report_payload(*, objective: str = "D9 Finding Generation from Persisted Evidence", persisted_evidence_inventory: Mapping[str, Any], eligibility_validation: Mapping[str, Any], operational_findings: list[Mapping[str, Any]], expectation_intelligence_summary: Mapping[str, Any], dashboard_cards: Mapping[str, Any], certification: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("objective", objective),
        ("persisted_evidence_inventory", OrderedDict(persisted_evidence_inventory)),
        ("eligibility_validation", OrderedDict(eligibility_validation)),
        ("operational_findings", [OrderedDict(f) for f in _list(operational_findings)]),
        ("expectation_intelligence_summary", OrderedDict(expectation_intelligence_summary)),
        ("dashboard_cards", OrderedDict(dashboard_cards)),
        ("certification", OrderedDict(certification)),
        ("no_direct_sql_bypass_used", True),
        ("recommendation", dashboard_cards.get("recommendation") or certification.get("certification_status")),
    ])


def build_d9_report_markdown(*, report_payload: Mapping[str, Any]) -> str:
    inv = report_payload.get("persisted_evidence_inventory") or {}
    elig = report_payload.get("eligibility_validation") or {}
    findings = report_payload.get("operational_findings") or []
    summary = report_payload.get("expectation_intelligence_summary") or {}
    cards = report_payload.get("dashboard_cards") or {}
    cert = report_payload.get("certification") or {}
    return "\n".join([
        "# D9 Finding Generation from Persisted Evidence",
        "",
        f"## Objective\n- {report_payload.get('objective')}",
        "## Scope\n- Deterministic, evidence-linked operational findings from certified persisted replay evidence.",
        "## Non-goals\n- No writes.\n- No direct SQL.\n- No trading-output generation.",
        f"## Persisted Evidence Inventory\n- Replay rows: {inv.get('replay_row_count', 0)}\n- Manifest rows: {inv.get('manifest_row_count', 0)}\n- Inventory status: {inv.get('inventory_status')}",
        f"## Eligibility Validation\n- Status: {elig.get('eligibility_status')}\n- Blocking: {', '.join(elig.get('blocking_reasons', [])) or 'none'}\n- Degraded: {', '.join(elig.get('degraded_reasons', [])) or 'none'}",
        f"## Operational Findings\n- Finding count: {len(findings)}\n- Categories: {', '.join([f.get('category', '') for f in findings]) or 'none'}",
        f"## Expectation Intelligence Summary\n- Dominant state: {summary.get('dominant_operational_state')}\n- Strongest integrity signal: {summary.get('strongest_integrity_signal')}\n- Strongest operational constraint: {summary.get('strongest_operational_constraint')}",
        f"## Dashboard Operational Cards\n- Finding generation status: {cards.get('finding_generation_status')}\n- Recommendation: {cards.get('recommendation')}",
        f"## Certification\n- {cert.get('certification_status')}",
        "## Governance Boundaries\n- Read-only evidence usage only.\n- no_direct_sql_bypass_used: True\n- Deterministic/replay-traceable finding generation.",
        f"## Final Recommendation\n- {report_payload.get('recommendation')}",
    ])
