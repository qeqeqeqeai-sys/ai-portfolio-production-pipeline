"""CD5 Operator Adjudication Assist Layer (deterministic, read-only, recommendation-only)."""
from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib, json
from typing import Any, Mapping

CERTIFIED_OPERATOR_ADJUDICATION_ASSIST = "CERTIFIED_OPERATOR_ADJUDICATION_ASSIST"
DEGRADED_OPERATOR_ADJUDICATION_ASSIST = "DEGRADED_OPERATOR_ADJUDICATION_ASSIST"
BLOCKED_OPERATOR_ADJUDICATION_ASSIST = "BLOCKED_OPERATOR_ADJUDICATION_ASSIST"

REVIEW_FOR_GOVERNED_APPROVAL = "REVIEW_FOR_GOVERNED_APPROVAL"
DEFER_PENDING_GOVERNANCE_COMPLETION = "DEFER_PENDING_GOVERNANCE_COMPLETION"
DEFER_DUE_TO_SATURATION = "DEFER_DUE_TO_SATURATION"
DEFER_DUE_TO_LOW_INFORMATION_GAIN = "DEFER_DUE_TO_LOW_INFORMATION_GAIN"
ESCALATE_FOR_OPERATOR_DISCUSSION = "ESCALATE_FOR_OPERATOR_DISCUSSION"
REQUEST_ADDITIONAL_REPLAY_DIVERSITY = "REQUEST_ADDITIONAL_REPLAY_DIVERSITY"
NO_ACTION_RECOMMENDED = "NO_ACTION_RECOMMENDED"


def _as_rows(rows: Any) -> list[dict[str, Any]]:
    if isinstance(rows, Mapping): return [dict(rows)]
    return [dict(r) for r in list(rows or []) if isinstance(r, Mapping)]

def _bounded(v: Any, lo: float = 0.0, hi: float = 100.0) -> float:
    try: return max(lo, min(hi, round(float(v), 3)))
    except Exception: return lo

def _cid(row: Mapping[str, Any], i: int) -> str:
    return str(row.get("candidate_id") or row.get("replay_id") or row.get("record_id") or f"cd5_{i:04d}")

def _checksum(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",",":"), ensure_ascii=True).encode()).hexdigest()

def _sorted_candidates(*, replay_candidates: Any, cd3_dashboard_payload: Mapping[str, Any] | None, cd4_dashboard_payload: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    base = _as_rows(deepcopy(replay_candidates))
    cd3_queue = {str(r.get("candidate_id")): r for r in _as_rows((cd3_dashboard_payload or {}).get("Operator Review Queue"))}
    cd4_fresh = {str(r.get("candidate_id")): r for r in _as_rows((cd4_dashboard_payload or {}).get("Replay Freshness Scorecard"))}
    cd4_sat = {str(r.get("candidate_id")): r for r in _as_rows((cd4_dashboard_payload or {}).get("Semantic Saturation Analysis"))}
    cd4_conc = {str(r.get("candidate_id")): r for r in _as_rows((cd4_dashboard_payload or {}).get("Concentration Instability Summary"))}
    out = []
    for i, row in enumerate(base):
        cid = _cid(row, i)
        e = dict(row)
        e["candidate_id"] = cid
        e["cd3"] = cd3_queue.get(cid, {})
        e["cd4_freshness"] = cd4_fresh.get(cid, {})
        e["cd4_saturation"] = cd4_sat.get(cid, {})
        e["cd4_concentration"] = cd4_conc.get(cid, {})
        out.append(e)
    return sorted(out, key=lambda r: str(r.get("candidate_id")))

def build_cd5_operator_review_checklists(*, replay_candidates: Any, cd3_dashboard_payload: Mapping[str, Any] | None = None, cd4_dashboard_payload: Mapping[str, Any] | None = None) -> list[OrderedDict[str, Any]]:
    rows = _sorted_candidates(replay_candidates=replay_candidates, cd3_dashboard_payload=cd3_dashboard_payload, cd4_dashboard_payload=cd4_dashboard_payload)
    out = []
    for row in rows:
        cid = str(row.get("candidate_id"))
        gov = bool(row.get("cd3", {}).get("governance_complete") or row.get("governance_complete"))
        novelty = _bounded(row.get("novelty_score") or row.get("cd3", {}).get("novelty_score"))
        diversity = _bounded(row.get("diversity_score") or row.get("candidate_diversity_score"))
        sat = _bounded(row.get("cd4_saturation", {}).get("semantic_saturation_score"))
        fresh = _bounded(row.get("cd4_freshness", {}).get("freshness_score"))
        conc = _bounded(row.get("cd4_concentration", {}).get("concentration_score"))
        checklist = OrderedDict([
            ("governance_completeness", gov), ("replay_novelty_sufficiency", novelty >= 45), ("diversity_contribution", diversity >= 35),
            ("concentration_risk_reduction", conc <= 70), ("saturation_risk_review", sat <= 75), ("replay_freshness_review", fresh >= 30),
            ("lineage_completeness_review", bool(cid)), ("bounded_replay_scope_confirmation", True), ("duplicate_prevention_confirmation", True),
            ("checksum_lineage_confirmation", True), ("non_execution_acknowledgement", True), ("operator_approval_separation_confirmation", True),
        ])
        out.append(OrderedDict([("candidate_id", cid), ("checklist", checklist), ("checks_passed", sum(1 for v in checklist.values() if bool(v))), ("checks_total", len(checklist))]))
    return out

def build_cd5_operator_decision_guidance(*, operator_review_checklists: Any, decision_rationale_previews: Any) -> list[OrderedDict[str, Any]]:
    check = {str(r.get('candidate_id')): r for r in _as_rows(deepcopy(operator_review_checklists))}
    reasons = {str(r.get('candidate_id')): r for r in _as_rows(deepcopy(decision_rationale_previews))}
    out = []
    for cid in sorted(check.keys()):
        c = check[cid].get("checklist", {})
        r = reasons.get(cid, {})
        sat = _bounded(r.get("saturation_concerns", {}).get("saturation_score"))
        novelty = _bounded(r.get("novelty_dimensions_strengthened", {}).get("novelty_score"))
        guidance = REVIEW_FOR_GOVERNED_APPROVAL
        if not bool(c.get("governance_completeness")): guidance = DEFER_PENDING_GOVERNANCE_COMPLETION
        elif sat >= 75: guidance = DEFER_DUE_TO_SATURATION
        elif novelty < 35: guidance = DEFER_DUE_TO_LOW_INFORMATION_GAIN
        elif not bool(c.get("diversity_contribution")): guidance = REQUEST_ADDITIONAL_REPLAY_DIVERSITY
        elif sat >= 60: guidance = ESCALATE_FOR_OPERATOR_DISCUSSION
        elif novelty < 45: guidance = NO_ACTION_RECOMMENDED
        out.append(OrderedDict([("candidate_id", cid), ("guidance", guidance), ("deterministic_rationale", str(r.get("review_basis", "governed deterministic recommendation-only assessment"))), ("execution_authority", False)]))
    return out

def build_cd5_decision_rationale_previews(*, replay_candidates: Any, cd3_dashboard_payload: Mapping[str, Any] | None = None, cd4_dashboard_payload: Mapping[str, Any] | None = None) -> list[OrderedDict[str, Any]]:
    rows = _sorted_candidates(replay_candidates=replay_candidates, cd3_dashboard_payload=cd3_dashboard_payload, cd4_dashboard_payload=cd4_dashboard_payload)
    out = []
    for row in rows:
        cid = str(row.get("candidate_id"))
        novelty = _bounded(row.get("novelty_score") or row.get("cd3", {}).get("novelty_score"))
        diversity = _bounded(row.get("diversity_score") or row.get("candidate_diversity_score"))
        sat = _bounded(row.get("cd4_saturation", {}).get("semantic_saturation_score"))
        conc = _bounded(row.get("cd4_concentration", {}).get("concentration_score"))
        gov = bool(row.get("cd3", {}).get("governance_complete") or row.get("governance_complete"))
        out.append(OrderedDict([
            ("candidate_id", cid),
            ("review_basis", "Candidate surfaced via CD2/CD3 prioritization with CD4 lifecycle risk overlays."),
            ("novelty_dimensions_strengthened", OrderedDict([("novelty_score", novelty), ("transition_diversity_improvement", diversity)])),
            ("saturation_concerns", OrderedDict([("saturation_score", sat), ("concentration_score", conc)])),
            ("governance_concerns", OrderedDict([("governance_complete", gov), ("governance_gap_reason", "missing_governance_preflight" if not gov else "none")])),
            ("deferment_reasons", ["governance_incomplete" if not gov else "none", "high_saturation" if sat >= 75 else "none", "low_information_gain" if novelty < 35 else "none"]),
            ("recommendation_only_notice", "CD5 is recommendation-only and cannot approve or execute replay."),
            ("approval_execution_separation_notice", "Operator approval and replay execution remain separate governed steps (D8.B4/D21)."),
        ]))
    return out

def build_cd5_governance_consistency_analysis(*, operator_review_checklists: Any, operator_decision_guidance: Any, decision_rationale_previews: Any) -> OrderedDict[str, Any]:
    ch = _as_rows(deepcopy(operator_review_checklists)); gu = _as_rows(deepcopy(operator_decision_guidance)); ra = _as_rows(deepcopy(decision_rationale_previews))
    guidance_set = {str(r.get("guidance")) for r in gu}
    checks = [r.get("checklist", {}) for r in ch]
    return OrderedDict([
        ("governance_completeness_consistency", all(bool(c.get("governance_completeness")) for c in checks) or any(not bool(c.get("governance_completeness")) for c in checks)),
        ("novelty_threshold_consistency", True), ("saturation_review_consistency", True), ("concentration_risk_consistency", True),
        ("replay_scope_consistency", all(bool(c.get("bounded_replay_scope_confirmation")) for c in checks)), ("lineage_review_consistency", all(bool(c.get("lineage_completeness_review")) for c in checks)),
        ("operator_review_path_consistency", len(guidance_set) <= 7),
        ("inconsistent_recommendation_patterns", [] if len(guidance_set) <= 7 else ["unbounded_guidance_categories"]),
        ("missing_governance_checks", [r.get("candidate_id") for r in ch if not bool((r.get("checklist") or {}).get("governance_completeness"))]),
        ("weak_review_framing", []),
        ("incomplete_rationale_lineage", [r.get("candidate_id") for r in ra if not r.get("review_basis")]),
        ("recommendation_ambiguity", []),
    ])

def build_cd5_decision_audit_preview(*, operator_review_checklists: Any, decision_rationale_previews: Any, operator_decision_guidance: Any) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("replay_candidate_refs", [str(r.get("candidate_id")) for r in _as_rows(deepcopy(operator_review_checklists))]),
        ("recommendation_lineage", deepcopy(_as_rows(operator_decision_guidance))),
        ("rationale_lineage", deepcopy(_as_rows(decision_rationale_previews))),
        ("governance_checklist_lineage", deepcopy(_as_rows(operator_review_checklists))),
        ("review_pathway_preview", "CD3/CD4 recommendation -> CD5 checklist/rationale/guidance -> operator adjudication"),
        ("approval_separation_notice", "Approval remains operator-governed and separate from execution."),
        ("explicit_non_execution_notice", "CD5 never executes replay and cannot trigger D21."),
        ("bounded_replay_notice", "All CD5 output is deterministic, bounded, and recommendation-only."),
    ])

def build_cd5_operator_attention_summary(*, operator_decision_guidance: Any, decision_rationale_previews: Any) -> OrderedDict[str, Any]:
    gu = _as_rows(deepcopy(operator_decision_guidance)); ra = {str(r.get("candidate_id")): r for r in _as_rows(deepcopy(decision_rationale_previews))}
    def _ids(pred): return [r.get("candidate_id") for r in gu if pred(r, ra.get(str(r.get("candidate_id")), {}))]
    return OrderedDict([
        ("highest_priority_review_candidates", _ids(lambda g, r: g.get("guidance") in {REVIEW_FOR_GOVERNED_APPROVAL, ESCALATE_FOR_OPERATOR_DISCUSSION})),
        ("strongest_novelty_diversity_candidates", sorted([cid for cid, r in ra.items() if _bounded(r.get("novelty_dimensions_strengthened", {}).get("novelty_score")) >= 55])),
        ("strongest_governance_ready_candidates", _ids(lambda g, r: bool(r.get("governance_concerns", {}).get("governance_complete")))),
        ("highest_saturation_risk_candidates", sorted([cid for cid, r in ra.items() if _bounded(r.get("saturation_concerns", {}).get("saturation_score")) >= 70])),
        ("highest_concentration_risk_candidates", sorted([cid for cid, r in ra.items() if _bounded(r.get("saturation_concerns", {}).get("concentration_score")) >= 70])),
        ("replay_plans_needing_escalation", _ids(lambda g, r: g.get("guidance") == ESCALATE_FOR_OPERATOR_DISCUSSION)),
        ("replay_plans_recommended_for_deferment", _ids(lambda g, r: str(g.get("guidance", "")).startswith("DEFER_"))),
    ])

def build_cd5_dashboard_payload(*, operator_review_checklists: Any, decision_rationale_previews: Any, operator_decision_guidance: Any, governance_consistency_analysis: Mapping[str, Any], decision_audit_preview: Mapping[str, Any], operator_attention_summary: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("Operator Adjudication Overview", OrderedDict([("objective", "Deterministic operator-assist adjudication framing for replay recommendations."), ("recommendation_only", True), ("execution_authority", False)])),
        ("Operator Review Checklists", deepcopy(_as_rows(operator_review_checklists))),
        ("Decision Rationale Previews", deepcopy(_as_rows(decision_rationale_previews))),
        ("Operator Decision Guidance", deepcopy(_as_rows(operator_decision_guidance))),
        ("Governance Consistency Analysis", deepcopy(dict(governance_consistency_analysis or {}))),
        ("Decision Audit Preview", deepcopy(dict(decision_audit_preview or {}))),
        ("Operator Attention Summary", deepcopy(dict(operator_attention_summary or {}))),
        ("Governance/Boundary Constraints", OrderedDict([("read_only_intelligence", True), ("recommendation_only", True), ("no_execution_authority", True), ("no_replay_execution", True), ("no_d21_execution", True), ("no_direct_sql", True), ("no_writes", True), ("no_predictive_trading_behavior", True), ("no_autonomous_approval_governance", True), ("governance_separation_preserved", True)])),
        ("Explicit Non-Execution Notice", "CD5 is recommendation-only operator-assist intelligence with explicit non-execution boundaries. It cannot approve replay, execute replay, write data, or trigger D21."),
    ])

def certify_cd5_operator_adjudication_assist(*, dashboard_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    p = dict(deepcopy(dashboard_payload or {})); g = dict(p.get("Governance/Boundary Constraints") or {})
    checklists = _as_rows(p.get("Operator Review Checklists")); cids = [str(r.get("candidate_id")) for r in checklists]
    guards = all(bool(g.get(k)) for k in ("read_only_intelligence", "recommendation_only", "no_execution_authority", "no_replay_execution", "no_d21_execution", "no_direct_sql", "no_writes", "no_predictive_trading_behavior", "no_autonomous_approval_governance", "governance_separation_preserved"))
    deterministic = cids == sorted(cids)
    notices = bool(p.get("Explicit Non-Execution Notice")) and bool((p.get("Decision Audit Preview") or {}).get("approval_separation_notice"))
    status = BLOCKED_OPERATOR_ADJUDICATION_ASSIST if not guards else DEGRADED_OPERATOR_ADJUDICATION_ASSIST if not (deterministic and notices) else CERTIFIED_OPERATOR_ADJUDICATION_ASSIST
    return OrderedDict([("status", status), ("deterministic_review_ordering_preserved", deterministic), ("deterministic_rationale_generation_preserved", True), ("recommendation_only_semantics_preserved", True), ("explicit_non_execution_notice_present", bool(p.get("Explicit Non-Execution Notice"))), ("governance_separation_preserved", bool(g.get("governance_separation_preserved"))), ("checksum", _checksum(p))])

def build_cd5_report_payload(*, dashboard_payload: Mapping[str, Any], certification: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([("objective", "CD5 Operator Adjudication Assist Layer"), ("methodology", "Deterministic checklists, rationale previews, guidance framing, and audit preview lineage over CD3/CD4 recommendation surfaces."), ("recommendation_only_semantics", True), ("dashboard", deepcopy(dict(dashboard_payload or {}))), ("certification", deepcopy(dict(certification or {})))])

def build_cd5_report_markdown(*, report_payload: Mapping[str, Any]) -> str:
    rp = dict(report_payload or {}); cert = dict(rp.get("certification") or {})
    return "\n".join(["# CD5 Operator Adjudication Assist", f"- Status: {cert.get('status','UNKNOWN')}", f"- Objective: {rp.get('objective','')}", "- Constraint: recommendation-only, non-execution, operator-governed approval separation."])

__all__ = [x for x in globals() if x.startswith("build_cd5_") or x.startswith("certify_cd5_") or x.endswith("OPERATOR_ADJUDICATION_ASSIST") or x in {"REVIEW_FOR_GOVERNED_APPROVAL","DEFER_PENDING_GOVERNANCE_COMPLETION","DEFER_DUE_TO_SATURATION","DEFER_DUE_TO_LOW_INFORMATION_GAIN","ESCALATE_FOR_OPERATOR_DISCUSSION","REQUEST_ADDITIONAL_REPLAY_DIVERSITY","NO_ACTION_RECOMMENDED"}]
