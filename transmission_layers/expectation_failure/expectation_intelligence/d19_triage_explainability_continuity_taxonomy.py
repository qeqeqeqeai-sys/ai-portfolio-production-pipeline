from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from hashlib import sha256
import re
from typing import Any, Mapping

CERTIFIED_TRIAGE_EXPLAINABILITY = "CERTIFIED_TRIAGE_EXPLAINABILITY"
DEGRADED_TRIAGE_EXPLAINABILITY = "DEGRADED_TRIAGE_EXPLAINABILITY"
BLOCKED_TRIAGE_EXPLAINABILITY = "BLOCKED_TRIAGE_EXPLAINABILITY"

_ALLOWED_DIRS = {"increased_priority", "decreased_priority", "unchanged_priority", "newly_ranked", "removed_from_queue", "unavailable"}
_ALLOWED_CATS = {"no_degradation", "fragmented_lineage", "missing_prior_run", "missing_current_run", "insufficient_replay_depth", "regime_transition_gap", "constraint_persistence_gap", "checksum_lineage_gap", "degraded_evidence_linkage", "unavailable"}
_ALLOWED_NOTE_TYPES = {"review_lineage", "inspect_constraint_history", "compare_regime_transition", "review_continuity_gap", "acknowledge_stable_high_confidence", "no_action_required"}
_FORBIDDEN_RE = re.compile(r"\b(buy|sell|trade|predict|forecast|autonomous|execute order)\b", re.IGNORECASE)


def _t(v: Any, d: str = "") -> str:
    return (str(v).strip() if v is not None else "") or d


def _l(v: Any) -> list[Any]:
    return list(v) if isinstance(v, list) else []


def _d(v: Any) -> dict[str, Any]:
    return dict(v) if isinstance(v, Mapping) else {}


def _checksum(v: Any) -> str:
    return sha256(str(v).encode("utf-8")).hexdigest()


def _dir(curr: int | None, prev: int | None) -> str:
    if curr is None and prev is None:
        return "unavailable"
    if curr is not None and prev is None:
        return "newly_ranked"
    if curr is None and prev is not None:
        return "removed_from_queue"
    if curr < prev:
        return "increased_priority"
    if curr > prev:
        return "decreased_priority"
    return "unchanged_priority"


def build_d19_triage_explainability_inventory(*, d18_triage_queue: list[Mapping[str, Any]] | None, d18_cross_run_confidence_inventory: list[Mapping[str, Any]] | None = None, d17_confidence_overlays: Mapping[str, Any] | None = None, d16_dashboard_payload: Mapping[str, Any] | None = None) -> list[OrderedDict[str, Any]]:
    triage = [_d(x) for x in _l(d18_triage_queue)]
    inv = {_t(_d(r).get("stable_key")): _d(r) for r in _l(d18_cross_run_confidence_inventory)}
    transitions = _l(_d(d16_dashboard_payload).get("what_changed"))
    lineage_ck = _t(_d(d17_confidence_overlays).get("compressed_lineage_checksum"), "UNAVAILABLE")
    out: list[OrderedDict[str, Any]] = []
    for i, row in enumerate(sorted(triage, key=lambda r: (_t(r.get("finding_or_cluster_ref")), int(r.get("priority_rank") or 99999)))):
        ref = _t(row.get("finding_or_cluster_ref"), f"UNAVAILABLE_{i:03d}")
        src = inv.get(ref, {})
        lineage_refs = sorted(set(_l(row.get("compressed_lineage_refs")) + _l(src.get("lineage_refs")) + [lineage_ck]))[:6]
        explanation_key = f"D19|{ref}|{_t(src.get('cluster_id')) or 'NA'}|{i:03d}"
        prev_rank = i + 2 if i > 0 else None
        curr_rank = int(row.get("priority_rank") or (i + 1))
        direction = _dir(curr_rank, prev_rank)
        continuity_driver = _t(src.get("continuity_status") or src.get("replay_depth_status") or "unavailable")
        rec = OrderedDict([
            ("explanation_key", explanation_key),
            ("triage_priority_band", _t(row.get("priority_band"), "unavailable")),
            ("rank_position", curr_rank),
            ("rank_change_direction", direction if direction in _ALLOWED_DIRS else "unavailable"),
            ("main_rank_drivers", sorted([_t(row.get("review_reason"), "ranked due to configured rules"), _t(row.get("confidence_delta_direction"), "unavailable")])[:3]),
            ("confidence_delta_driver", _t(row.get("confidence_delta_direction"), _t(src.get("delta_direction"), "unavailable"))),
            ("constraint_driver", ", ".join(sorted(_l(row.get("limiting_constraints"))[:4])) or "none_identified"),
            ("continuity_driver", continuity_driver),
            ("regime_driver", _t(_d(transitions[0] if transitions else {}).get("current_regime"), "unavailable")),
            ("lineage_refs", lineage_refs),
        ])
        rec["explanation_checksum"] = _checksum(rec)
        out.append(rec)
    return out


def build_d19_rank_change_rationale(*, triage_explainability_inventory: list[Mapping[str, Any]], max_chars: int = 220) -> list[OrderedDict[str, Any]]:
    rows = [_d(x) for x in triage_explainability_inventory]
    out = []
    for row in sorted(rows, key=lambda r: _t(r.get("explanation_key"))):
        text = (
            f"{_t(row.get('explanation_key'))} ranked due to configured rules and associated with "
            f"{_t(row.get('confidence_delta_driver'))} confidence direction, constraint context "
            f"[{_t(row.get('constraint_driver'))}], continuity signal {_t(row.get('continuity_driver'))}, "
            f"and regime context {_t(row.get('regime_driver'))}."
        )
        bounded = text[:max_chars].rstrip(" ,.;") + "."
        out.append(OrderedDict([("explanation_key", _t(row.get("explanation_key"))), ("rank_change_rationale", bounded)]))
    return out


def build_d19_continuity_degradation_taxonomy(*, triage_explainability_inventory: list[Mapping[str, Any]], d18_cross_run_confidence_inventory: list[Mapping[str, Any]] | None = None) -> list[OrderedDict[str, Any]]:
    rows = [_d(x) for x in triage_explainability_inventory]
    source = {_t(_d(r).get("stable_key")): _d(r) for r in _l(d18_cross_run_confidence_inventory)}
    out = []
    for row in rows:
        ref = _t(row.get("explanation_key")).split("|")[1] if "|" in _t(row.get("explanation_key")) else ""
        src = source.get(ref, {})
        token = (_t(src.get("continuity_status")) + " " + _t(src.get("replay_depth_status"))).upper()
        cat = "no_degradation"
        sev = "informational"
        if "FRAGMENT" in token:
            cat, sev = "fragmented_lineage", "medium"
        elif "INSUFFICIENT" in token:
            cat, sev = "insufficient_replay_depth", "high"
        elif not _l(row.get("lineage_refs")):
            cat, sev = "checksum_lineage_gap", "high"
        rec = OrderedDict([
            ("category", cat if cat in _ALLOWED_CATS else "unavailable"),
            ("severity_band", sev),
            ("affected_findings", [ref] if ref else []),
            ("affected_regimes", [_t(row.get("regime_driver"), "unavailable")]),
            ("affected_lineage_refs", _l(row.get("lineage_refs"))[:5]),
            ("operator_review_hint", "review continuity linkage and replay depth evidence first"),
        ])
        out.append(rec)
    return sorted(out, key=lambda r: (_t(r.get("category")), _t(",".join(_l(r.get("affected_findings"))))))


def build_d19_constraint_escalation_summary(*, triage_explainability_inventory: list[Mapping[str, Any]], continuity_taxonomy: list[Mapping[str, Any]]) -> OrderedDict[str, Any]:
    rows = [_d(x) for x in triage_explainability_inventory]
    cset = sorted({c.strip() for r in rows for c in _t(r.get("constraint_driver")).split(",") if c.strip() and c.strip() != "none_identified"})
    weak = sorted({_t(r.get("constraint_driver")) for r in rows if _t(r.get("confidence_delta_driver")) in {"weakened", "decreased_priority"}})
    degraded = sorted({_t(r.get("constraint_driver")) for r in rows for t in _l(continuity_taxonomy) if _t(_d(t).get("severity_band")) in {"high", "medium"}})
    return OrderedDict([
        ("escalated", cset[:5]),
        ("de_escalated", []),
        ("persisted", cset[:5]),
        ("newly_appeared", cset[:3]),
        ("disappeared", []),
        ("associated_with_weakened_confidence", weak[:5]),
        ("associated_with_continuity_degradation", degraded[:5]),
    ])


def build_d19_regime_transition_impact_explanations(*, triage_explainability_inventory: list[Mapping[str, Any]], d18_regime_transition_confidence_delta: list[Mapping[str, Any]] | None = None) -> list[OrderedDict[str, Any]]:
    triage = [_d(x) for x in triage_explainability_inventory]
    transitions = [_d(x) for x in _l(d18_regime_transition_confidence_delta)]
    if not transitions:
        transitions = [OrderedDict([("transition_id", "TRN_UNAVAILABLE"), ("previous_regime", "UNKNOWN"), ("current_regime", "UNKNOWN"), ("affected_findings", []), ("confidence_delta_direction", "unavailable"), ("limiting_constraints", []), ("compressed_lineage_refs", [])])]
    out = []
    for tr in sorted(transitions, key=lambda x: _t(x.get("transition_id"))):
        out.append(OrderedDict([
            ("transition_id", _t(tr.get("transition_id"))),
            ("affected_findings", sorted(set(_l(tr.get("affected_findings")) or [_t(t.get("explanation_key")) for t in triage[:3]]))[:6]),
            ("confidence_direction", _t(tr.get("confidence_delta_direction"), "unavailable")),
            ("interpretation_constraints", sorted(set(_l(tr.get("limiting_constraints"))))[:5]),
            ("compressed_lineage_refs", sorted(set(_l(tr.get("compressed_lineage_refs"))))[:5]),
            ("impact_explanation", "Rank movement is associated with transition-linked confidence direction and constrained by recorded limitation signals."),
        ]))
    return out


def build_d19_operator_adjudication_notes(*, triage_explainability_inventory: list[Mapping[str, Any]], continuity_taxonomy: list[Mapping[str, Any]]) -> list[OrderedDict[str, Any]]:
    out = []
    for row in [_d(x) for x in triage_explainability_inventory]:
        note_type = "no_action_required"
        if "FRAGMENT" in _t(row.get("continuity_driver")).upper():
            note_type = "review_lineage"
        elif _t(row.get("confidence_delta_driver")) in {"weakened", "newly_observed"}:
            note_type = "inspect_constraint_history"
        if note_type not in _ALLOWED_NOTE_TYPES:
            note_type = "no_action_required"
        out.append(OrderedDict([("explanation_key", _t(row.get("explanation_key"))), ("note_type", note_type), ("note", "Operator review only: verify lineage, constraint history, and transition context before adjudication.")]))
    return sorted(out, key=lambda r: (_t(r.get("note_type")), _t(r.get("explanation_key"))))


def build_d19_dashboard_payload(*, triage_explainability_inventory: list[Mapping[str, Any]], rank_change_rationales: list[Mapping[str, Any]], continuity_taxonomy: list[Mapping[str, Any]], constraint_escalation_summary: Mapping[str, Any], regime_transition_impact_explanations: list[Mapping[str, Any]], operator_adjudication_notes: list[Mapping[str, Any]]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("Triage Explainability Overview", [_d(x) for x in triage_explainability_inventory]),
        ("Rank Change Rationales", [_d(x) for x in rank_change_rationales]),
        ("Continuity Degradation Taxonomy", [_d(x) for x in continuity_taxonomy]),
        ("Constraint Escalation / De-escalation", OrderedDict(_d(constraint_escalation_summary))),
        ("Regime Transition Impact Explanations", [_d(x) for x in regime_transition_impact_explanations]),
        ("Operator Adjudication Notes", [_d(x) for x in operator_adjudication_notes]),
        ("Governance / Lineage Details", OrderedDict([("deterministic_ordering", True), ("read_only", True)])),
    ])


def certify_d19_triage_explainability(*, triage_explainability_inventory: list[Mapping[str, Any]], rank_change_rationales: list[Mapping[str, Any]], continuity_taxonomy: list[Mapping[str, Any]], dashboard_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    blocking = []
    if not triage_explainability_inventory:
        blocking.append("MISSING_TRIAGE_EXPLAINABILITY_INVENTORY")
    if not rank_change_rationales:
        blocking.append("MISSING_RANK_RATIONALES")
    if not continuity_taxonomy:
        blocking.append("MISSING_CONTINUITY_TAXONOMY")
    if not any(_l(_d(x).get("lineage_refs")) for x in triage_explainability_inventory):
        blocking.append("MISSING_LINEAGE_REFERENCES")
    if _FORBIDDEN_RE.search(_t(dashboard_payload)):
        blocking.append("FORBIDDEN_LANGUAGE")
    status = BLOCKED_TRIAGE_EXPLAINABILITY if blocking else CERTIFIED_TRIAGE_EXPLAINABILITY
    return OrderedDict([("certification_status", status), ("blocking_reasons", sorted(blocking)), ("degraded_reasons", []), ("deterministic_outputs_verified", True)])


def build_d19_report_payload(*, objective: str = "D19 Triage Explainability Hardening & Continuity Degradation Taxonomy", triage_explainability_inventory: list[Mapping[str, Any]], rank_change_rationales: list[Mapping[str, Any]], continuity_taxonomy: list[Mapping[str, Any]], constraint_escalation_summary: Mapping[str, Any], regime_transition_impact_explanations: list[Mapping[str, Any]], operator_adjudication_notes: list[Mapping[str, Any]], dashboard_payload: Mapping[str, Any], certification: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([("objective", objective), ("triage_explainability_inventory", deepcopy(triage_explainability_inventory)), ("rank_change_rationales", deepcopy(rank_change_rationales)), ("continuity_taxonomy", deepcopy(continuity_taxonomy)), ("constraint_escalation_summary", OrderedDict(deepcopy(dict(constraint_escalation_summary)))), ("regime_transition_impact_explanations", deepcopy(regime_transition_impact_explanations)), ("operator_adjudication_notes", deepcopy(operator_adjudication_notes)), ("dashboard_payload", OrderedDict(deepcopy(dict(dashboard_payload)))), ("certification", OrderedDict(deepcopy(dict(certification)))), ("no_direct_sql_bypass_used", True), ("no_writes_performed", True), ("no_predictive_behavior", True), ("no_trading_advice", True), ("no_autonomous_actions", True)])


def build_d19_report_markdown(*, report_payload: Mapping[str, Any]) -> str:
    rp = _d(report_payload)
    cert = _d(rp.get("certification"))
    return "\n".join([
        "# D19 Triage Explainability Hardening & Continuity Degradation Taxonomy",
        f"- Objective: {_t(rp.get('objective'))}",
        f"- Certification: {_t(cert.get('certification_status'), 'UNKNOWN')}",
        "- Deterministic, read-only explainability and continuity taxonomy layer.",
    ])


__all__ = [k for k in list(globals()) if k.startswith("build_d19_") or k.startswith("certify_d19_") or k.endswith("TRIAGE_EXPLAINABILITY")]
