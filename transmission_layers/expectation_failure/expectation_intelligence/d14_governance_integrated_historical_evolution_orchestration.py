from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from hashlib import sha256
from typing import Any, Mapping


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _checksum(parts: list[str]) -> str:
    return sha256("|".join(parts).encode("utf-8")).hexdigest()[:24].upper()


def build_d14_orchestration_inventory(*, d11_report_payload: Mapping[str, Any] | None, d12_report_payload: Mapping[str, Any] | None, d13_report_payload: Mapping[str, Any] | None) -> OrderedDict[str, Any]:
    d11 = _dict(d11_report_payload)
    d12 = _dict(d12_report_payload)
    d13 = _dict(d13_report_payload)

    d11_cert = _text(_dict(d11.get("certification")).get("certification_status"))
    d12_cert = _text(_dict(d12.get("certification")).get("certification_status"))
    d13_cert = _text(_dict(d13.get("certification")).get("certification_status"))

    replay_depth = _text(_dict(d12.get("expectation_intelligence_synthesis")).get("replay_depth_interpretation")) or _text(_dict(d13.get("current_snapshot")).get("replay_depth_interpretation")) or "INSUFFICIENT"
    regime = _text(_dict(d12.get("regime_classification")).get("historical_expectation_regime")) or _text(_dict(d13.get("current_snapshot")).get("historical_expectation_regime")) or "UNSPECIFIED_REGIME"
    evolution = _text(_dict(d13.get("regime_evolution_classification")).get("regime_evolution_class")) or "REGIME_INSUFFICIENT_HISTORY"
    continuity = _text(_dict(d12.get("expectation_intelligence_synthesis")).get("continuity_interpretation")) or "fragmented"

    d12_patterns = _list(d12.get("cross_window_patterns"))
    pattern_count = len(d12_patterns)

    unresolved = sorted({_text(x) for x in _list(_dict(d12.get("expectation_intelligence_synthesis")).get("unresolved_constraints")) if _text(x)})
    if not unresolved:
        unresolved = sorted({_text(x) for x in _list(_dict(d13.get("current_snapshot")).get("unresolved_constraints")) if _text(x)})

    lineage_refs = sorted({
        *[_text(x) for x in _list(_dict(d11.get("historical_replay_windows")).get("lineage_refs")) if _text(x)],
        *[_text(x) for x in _list(_dict(d12.get("historical_expectation_inventory")).get("lineage_refs")) if _text(x)],
        *[_text(x) for x in _list(_dict(d13.get("current_snapshot")).get("lineage_refs")) if _text(x)],
    })

    missing_payloads = not (d11 and d12 and d13)
    continuity_fragmented = "fragment" in continuity.lower()
    blocked = missing_payloads or d13_cert.startswith("BLOCKED") or not lineage_refs or continuity_fragmented or "insufficient" in replay_depth.lower()
    degraded = d11_cert.startswith("DEGRADED") or d12_cert.startswith("DEGRADED") or d13_cert.startswith("DEGRADED") or bool(unresolved)

    if blocked:
        inv_status = "ORCHESTRATION_BLOCKED"
    elif degraded:
        inv_status = "ORCHESTRATION_DEGRADED"
    else:
        inv_status = "ORCHESTRATION_READY"

    checksum = _checksum([d11_cert, d12_cert, d13_cert, replay_depth, regime, evolution, continuity, str(pattern_count), ",".join(unresolved), ",".join(lineage_refs), inv_status])
    return OrderedDict([
        ("d11_certification_status", d11_cert),
        ("d12_certification_status", d12_cert),
        ("d13_certification_status", d13_cert),
        ("replay_depth_assessment", replay_depth),
        ("historical_expectation_regime", regime),
        ("regime_evolution_class", evolution),
        ("continuity_status", continuity),
        ("pattern_count", pattern_count),
        ("unresolved_constraints", unresolved),
        ("lineage_refs", lineage_refs),
        ("inventory_status", inv_status),
        ("inventory_checksum", checksum),
    ])


def validate_d14_orchestration_eligibility(*, d11_report_payload: Mapping[str, Any] | None, d12_report_payload: Mapping[str, Any] | None, d13_report_payload: Mapping[str, Any] | None, orchestration_inventory: Mapping[str, Any]) -> OrderedDict[str, Any]:
    inv = _dict(orchestration_inventory)
    blocking, degraded = [], []
    if not (_dict(d11_report_payload) and _dict(d12_report_payload) and _dict(d13_report_payload)):
        blocking.append("MISSING_REQUIRED_D11_D12_D13_PAYLOADS")
    if _text(inv.get("d13_certification_status")).startswith("BLOCKED"):
        blocking.append("D13_CERTIFICATION_BLOCKED")
    if not _list(inv.get("lineage_refs")):
        blocking.append("MISSING_LINEAGE_REFS")
    if "fragment" in _text(inv.get("continuity_status")).lower():
        blocking.append("CONTINUITY_FRAGMENTED")
    if "insufficient" in _text(inv.get("replay_depth_assessment")).lower():
        blocking.append("REPLAY_DEPTH_INSUFFICIENT")

    if _text(inv.get("inventory_status")) == "ORCHESTRATION_DEGRADED":
        degraded.append("ORCHESTRATION_INVENTORY_DEGRADED")
    if _text(inv.get("d11_certification_status")).startswith("DEGRADED"):
        degraded.append("D11_DEGRADED")
    if _text(inv.get("d12_certification_status")).startswith("DEGRADED"):
        degraded.append("D12_DEGRADED")
    if _text(inv.get("d13_certification_status")).startswith("DEGRADED"):
        degraded.append("D13_DEGRADED")

    if blocking:
        status = "ORCHESTRATION_BLOCKED"
    elif degraded:
        status = "ORCHESTRATION_DEGRADED"
    else:
        status = "ORCHESTRATION_ELIGIBLE"
    return OrderedDict([("eligibility_status", status), ("blocking_reasons", blocking), ("degraded_reasons", degraded)])


def build_d14_supervisory_rollup(*, orchestration_inventory: Mapping[str, Any], eligibility_validation: Mapping[str, Any], audit_continuity: Mapping[str, Any]) -> OrderedDict[str, Any]:
    inv, elg, audit = _dict(orchestration_inventory), _dict(eligibility_validation), _dict(audit_continuity)
    unresolved = _list(inv.get("unresolved_constraints"))
    unresolved_count = len(unresolved)
    base = 100
    penalty = 0
    if _text(elg.get("eligibility_status")) == "ORCHESTRATION_BLOCKED":
        penalty += 60
    elif _text(elg.get("eligibility_status")) == "ORCHESTRATION_DEGRADED":
        penalty += 25
    if _text(audit.get("audit_continuity_status")) == "AUDIT_CONTINUITY_FRAGMENTED":
        penalty += 25
    elif _text(audit.get("audit_continuity_status")) == "AUDIT_CONTINUITY_DEGRADED":
        penalty += 10
    penalty += min(unresolved_count, 15)
    rollup_score = max(0, min(100, base - penalty))

    state = "SUPERVISORY_OPERATIONAL_STABLE" if rollup_score >= 75 else ("SUPERVISORY_OPERATIONAL_DEGRADED" if rollup_score >= 40 else "SUPERVISORY_OPERATIONAL_BLOCKED")
    risk = "LOW" if rollup_score >= 80 else ("MEDIUM" if rollup_score >= 50 else "HIGH")
    confidence = "HIGH" if _text(elg.get("eligibility_status")) == "ORCHESTRATION_ELIGIBLE" else ("MEDIUM" if _text(elg.get("eligibility_status")) == "ORCHESTRATION_DEGRADED" else "LOW")
    return OrderedDict([
        ("supervisory_operational_state", state),
        ("dominant_historical_regime", inv.get("historical_expectation_regime") or "UNSPECIFIED_REGIME"),
        ("regime_evolution_interpretation", inv.get("regime_evolution_class") or "REGIME_INSUFFICIENT_HISTORY"),
        ("replay_depth_interpretation", inv.get("replay_depth_assessment") or "UNSPECIFIED"),
        ("continuity_interpretation", inv.get("continuity_status") or "UNSPECIFIED"),
        ("strongest_recurring_constraint", unresolved[0] if unresolved else "NONE"),
        ("strongest_evolution_driver", "constraint_persistence" if unresolved else "regime_transition_stability"),
        ("evidence_confidence_band", confidence),
        ("supervisory_risk_band", risk),
        ("unresolved_constraint_count", unresolved_count),
        ("rollup_score", rollup_score),
    ])


def build_d14_cross_phase_audit_continuity(*, d11_report_payload: Mapping[str, Any] | None, d12_report_payload: Mapping[str, Any] | None, d13_report_payload: Mapping[str, Any] | None) -> OrderedDict[str, Any]:
    d11, d12, d13 = _dict(d11_report_payload), _dict(d12_report_payload), _dict(d13_report_payload)
    d11_refs = sorted({_text(x) for x in _list(_dict(d11.get("historical_replay_windows")).get("lineage_refs")) if _text(x)})
    d12_refs = sorted({_text(x) for x in _list(_dict(d12.get("historical_expectation_inventory")).get("lineage_refs")) if _text(x)})
    d13_refs = sorted({_text(x) for x in _list(_dict(d13.get("current_snapshot")).get("lineage_refs")) if _text(x)})
    common = sorted(set(d11_refs) & set(d12_refs) & set(d13_refs))
    all_refs = sorted(set(d11_refs) | set(d12_refs) | set(d13_refs))
    missing = sorted(set(all_refs) - set(common))
    if not all_refs or not common:
        status = "AUDIT_CONTINUITY_FRAGMENTED"
    elif missing:
        status = "AUDIT_CONTINUITY_DEGRADED"
    else:
        status = "AUDIT_CONTINUITY_OK"
    return OrderedDict([
        ("continuity_chain", OrderedDict([("d11_replay_windows", _list(_dict(d11.get("historical_replay_windows")).get("replay_windows"))), ("d12_expectation_patterns", _list(d12.get("cross_window_patterns"))), ("d13_regime_evolution_deltas", _dict(d13.get("delta_comparison")))])),
        ("lineage_chain", OrderedDict([("d11", d11_refs), ("d12", d12_refs), ("d13", d13_refs), ("common", common)])),
        ("phase_alignment_status", "PHASE_ALIGNMENT_OK" if common else "PHASE_ALIGNMENT_MISSING"),
        ("missing_alignment_refs", missing),
        ("audit_continuity_status", status),
    ])


def build_d14_supervisory_operational_narrative(*, orchestration_inventory: Mapping[str, Any], supervisory_rollup: Mapping[str, Any], audit_continuity: Mapping[str, Any], certification: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    inv, roll, audit, cert = _dict(orchestration_inventory), _dict(supervisory_rollup), _dict(audit_continuity), _dict(certification)
    unresolved = _list(inv.get("unresolved_constraints"))
    return OrderedDict([
        ("dominant_supervisory_state", roll.get("supervisory_operational_state")),
        ("strongest_integrity_signal", audit.get("audit_continuity_status")),
        ("strongest_historical_constraint", roll.get("strongest_recurring_constraint")),
        ("strongest_evolutionary_change", inv.get("regime_evolution_class")),
        ("historical_interpretation", f"Historical regime is {_text(roll.get('dominant_historical_regime'))}."),
        ("continuity_interpretation", f"Cross-phase continuity status is {_text(audit.get('audit_continuity_status'))}."),
        ("governance_interpretation", "Governance boundaries retained with deterministic orchestration and replay traceability."),
        ("supervisory_interpretation", f"Supervisory posture: {_text(roll.get('supervisory_operational_state'))}; risk band {_text(roll.get('supervisory_risk_band'))}."),
        ("unresolved_constraints", unresolved),
        ("caveats", ["Interpretive supervisory orchestration only", "No predictive, trading, alerting, or autonomous behavior", _text(cert.get("certification_status")) or "Certification pending"]),
    ])


def certify_d14_historical_evolution_orchestration(*, d13_report_payload: Mapping[str, Any] | None, eligibility_validation: Mapping[str, Any], audit_continuity: Mapping[str, Any], supervisory_rollup: Mapping[str, Any], orchestration_inventory: Mapping[str, Any]) -> OrderedDict[str, Any]:
    d13 = _dict(d13_report_payload)
    elg, audit, roll, inv = _dict(eligibility_validation), _dict(audit_continuity), _dict(supervisory_rollup), _dict(orchestration_inventory)
    d13_cert = _text(_dict(d13.get("certification")).get("certification_status"))
    blocked = []
    if not d13:
        blocked.append("MISSING_D13_PAYLOAD")
    if _text(elg.get("eligibility_status")) == "ORCHESTRATION_BLOCKED":
        blocked.append("ELIGIBILITY_BLOCKED")
    if _text(audit.get("audit_continuity_status")) == "AUDIT_CONTINUITY_FRAGMENTED":
        blocked.append("AUDIT_CONTINUITY_FRAGMENTED")
    if not _list(inv.get("lineage_refs")):
        blocked.append("MISSING_LINEAGE_REFS")
    if d13_cert.startswith("BLOCKED"):
        blocked.append("D13_BLOCKED")
    rollup_complete = all(k in roll for k in ["supervisory_operational_state", "rollup_score", "supervisory_risk_band"])
    if not rollup_complete:
        blocked.append("SUPERVISORY_ROLLUP_INCOMPLETE")

    if blocked:
        status = "BLOCKED_HISTORICAL_EVOLUTION_ORCHESTRATION"
    elif _text(elg.get("eligibility_status")) == "ORCHESTRATION_ELIGIBLE" and _text(audit.get("audit_continuity_status")) != "AUDIT_CONTINUITY_FRAGMENTED" and (d13_cert.startswith("CERTIFIED") or d13_cert.startswith("DEGRADED")):
        status = "CERTIFIED_HISTORICAL_EVOLUTION_ORCHESTRATION"
    else:
        status = "DEGRADED_HISTORICAL_EVOLUTION_ORCHESTRATION"
    return OrderedDict([("certification_status", status), ("blocking_reasons", blocked), ("lineage_intact", bool(_list(inv.get("lineage_refs")))), ("supervisory_rollup_complete", rollup_complete)])


def build_d14_dashboard_supervisory_cards(*, orchestration_inventory: Mapping[str, Any], supervisory_rollup: Mapping[str, Any], supervisory_operational_narrative: Mapping[str, Any], certification: Mapping[str, Any]) -> OrderedDict[str, Any]:
    inv, roll, nar, cert = _dict(orchestration_inventory), _dict(supervisory_rollup), _dict(supervisory_operational_narrative), _dict(certification)
    return OrderedDict([
        ("orchestration_status", cert.get("certification_status") or inv.get("inventory_status")),
        ("supervisory_operational_state", roll.get("supervisory_operational_state")),
        ("dominant_historical_regime", roll.get("dominant_historical_regime")),
        ("regime_evolution_class", inv.get("regime_evolution_class")),
        ("supervisory_risk_band", roll.get("supervisory_risk_band")),
        ("strongest_integrity_signal", nar.get("strongest_integrity_signal")),
        ("strongest_historical_constraint", nar.get("strongest_historical_constraint")),
        ("strongest_evolutionary_change", nar.get("strongest_evolutionary_change")),
        ("unresolved_constraint_count", roll.get("unresolved_constraint_count", 0)),
        ("recommendation", "Proceed with governed supervisory operationalization planning." if _text(cert.get("certification_status")).startswith("CERTIFIED") else "Resolve orchestration constraints before governed operationalization."),
    ])


def build_d14_report_payload(*, orchestration_inventory: Mapping[str, Any], eligibility_validation: Mapping[str, Any], supervisory_rollup: Mapping[str, Any], audit_continuity: Mapping[str, Any], supervisory_operational_narrative: Mapping[str, Any], dashboard_cards: Mapping[str, Any], certification: Mapping[str, Any], objective: str = "D14 Governance-Integrated Historical Evolution Orchestration") -> OrderedDict[str, Any]:
    return OrderedDict([
        ("objective", objective),
        ("orchestration_inventory", OrderedDict(deepcopy(dict(orchestration_inventory)))),
        ("eligibility_validation", OrderedDict(deepcopy(dict(eligibility_validation)))),
        ("supervisory_rollup", OrderedDict(deepcopy(dict(supervisory_rollup)))),
        ("audit_continuity", OrderedDict(deepcopy(dict(audit_continuity)))),
        ("supervisory_operational_narrative", OrderedDict(deepcopy(dict(supervisory_operational_narrative)))),
        ("dashboard_cards", OrderedDict(deepcopy(dict(dashboard_cards)))),
        ("certification", OrderedDict(deepcopy(dict(certification)))),
        ("no_direct_sql_bypass_used", True),
        ("no_writes_performed", True),
        ("no_live_fetches_performed", True),
        ("no_alerts_sent", True),
        ("no_predictive_behavior", True),
        ("recommendation", dashboard_cards.get("recommendation") or certification.get("certification_status")),
    ])


def build_d14_report_markdown(*, report_payload: Mapping[str, Any]) -> str:
    r = _dict(report_payload)
    return "\n".join([
        "# D14 Governance-Integrated Historical Evolution Orchestration",
        "",
        f"## Objective\n- {r.get('objective')}",
        "## Scope\n- Deterministic supervisory orchestration across D11/D12/D13 outputs.",
        "## Non-goals\n- No prediction.\n- No trading signals.\n- No alert dispatch.\n- No live ingestion.\n- No autonomous decisioning.",
        f"## Orchestration Inventory\n- {r.get('orchestration_inventory')}",
        f"## Eligibility Validation\n- {r.get('eligibility_validation')}",
        f"## Supervisory Rollup\n- {r.get('supervisory_rollup')}",
        f"## Cross-Phase Audit Continuity\n- {r.get('audit_continuity')}",
        f"## Supervisory Operational Narrative\n- {r.get('supervisory_operational_narrative')}",
        f"## Dashboard Cards\n- {r.get('dashboard_cards')}",
        f"## Certification\n- {r.get('certification')}",
        "## Governance Boundaries\n- no_direct_sql_bypass_used: True\n- no_writes_performed: True\n- no_live_fetches_performed: True\n- no_alerts_sent: True\n- no_predictive_behavior: True",
        f"## Final Recommendation\n- {r.get('recommendation')}",
    ])
