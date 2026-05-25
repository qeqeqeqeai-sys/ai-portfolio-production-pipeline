"""CD3 Governed Novelty-Guided Replay Expansion Plan (deterministic, read-only, plan-only)."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

CERTIFIED_GOVERNED_NOVELTY_GUIDED_REPLAY_EXPANSION_PLAN = "CERTIFIED_GOVERNED_NOVELTY_GUIDED_REPLAY_EXPANSION_PLAN"
DEGRADED_GOVERNED_NOVELTY_GUIDED_REPLAY_EXPANSION_PLAN = "DEGRADED_GOVERNED_NOVELTY_GUIDED_REPLAY_EXPANSION_PLAN"
BLOCKED_GOVERNED_NOVELTY_GUIDED_REPLAY_EXPANSION_PLAN = "BLOCKED_GOVERNED_NOVELTY_GUIDED_REPLAY_EXPANSION_PLAN"

ELIGIBLE_FOR_OPERATOR_REVIEW = "ELIGIBLE_FOR_OPERATOR_REVIEW"
DEFER_SATURATED_OR_REPETITIVE = "DEFER_SATURATED_OR_REPETITIVE"
DEFER_GOVERNANCE_INCOMPLETE = "DEFER_GOVERNANCE_INCOMPLETE"
DEFER_INSUFFICIENT_DATA = "DEFER_INSUFFICIENT_DATA"
DEFER_LOW_MARGINAL_INFORMATION = "DEFER_LOW_MARGINAL_INFORMATION"


def _as_rows(rows: Any) -> list[dict[str, Any]]:
    if isinstance(rows, Mapping):
        return [dict(rows)]
    return [dict(r) for r in list(rows or []) if isinstance(r, Mapping)]


def _stable_checksum(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _bounded(value: Any, default: float = 0.0) -> float:
    try:
        return max(0.0, min(1.0, round(float(value), 6)))
    except Exception:
        return default


def build_cd3_replay_expansion_candidate_set(*, cd2_candidate_pool: Any, cd2_novelty_scorecard: Any, cd2_priority_buckets: Mapping[str, Any] | None = None) -> list[OrderedDict[str, Any]]:
    pool_by_id = {str(r.get("candidate_id")): r for r in _as_rows(deepcopy(cd2_candidate_pool))}
    score_by_id = {str(r.get("candidate_id")): r for r in _as_rows(deepcopy(cd2_novelty_scorecard))}
    bucket_of: dict[str, str] = {}
    for bucket, ids in dict(cd2_priority_buckets or {}).items():
        for cid in ids or []:
            bucket_of[str(cid)] = str(bucket)

    candidate_ids = sorted(set(pool_by_id) | set(score_by_id) | set(bucket_of))
    out: list[OrderedDict[str, Any]] = []
    for cid in candidate_ids:
        pool = pool_by_id.get(cid, {})
        score = score_by_id.get(cid, {})
        bucket = bucket_of.get(cid, "INSUFFICIENT_DATA_CANDIDATE")
        sat = _bounded(score.get("semantic_saturation_penalty"), 1.0 if bucket == "SATURATED_OR_REPETITIVE_CANDIDATE" else 0.0)
        rep = _bounded(score.get("repeated_pattern_penalty"), 1.0 if bucket == "SATURATED_OR_REPETITIVE_CANDIDATE" else 0.0)
        gain = _bounded(score.get("marginal_structural_information_gain"), 0.0)
        gov_ready = _bounded(score.get("governance_readiness_modifier"), 0.0) >= 1.0 and bool(pool.get("governance_lineage_refs") or pool.get("lineage_refs"))
        missing = int(score.get("missing_dimension_count") or 0)
        if missing >= 4 or not pool:
            eligibility = DEFER_INSUFFICIENT_DATA
        elif bucket == "GOVERNANCE_INCOMPLETE_CANDIDATE" or not gov_ready:
            eligibility = DEFER_GOVERNANCE_INCOMPLETE
        elif bucket == "SATURATED_OR_REPETITIVE_CANDIDATE" or sat >= 0.6 or rep >= 0.6:
            eligibility = DEFER_SATURATED_OR_REPETITIVE
        elif bucket == "LOW_MARGINAL_INFORMATION_PRIORITY" or gain <= 0.25:
            eligibility = DEFER_LOW_MARGINAL_INFORMATION
        else:
            eligibility = ELIGIBLE_FOR_OPERATOR_REVIEW
        out.append(OrderedDict([
            ("candidate_id", cid),
            ("replay_window_ref", pool.get("replay_window_ref") or cid),
            ("priority_bucket", bucket),
            ("novelty_score_summary", OrderedDict([("marginal_structural_information_gain", gain), ("transition_signature_rarity", _bounded(score.get("transition_signature_rarity"))), ("semantic_theme_novelty", _bounded(score.get("semantic_theme_novelty")))])),
            ("diversity_dimensions_strengthened", "contradiction/continuity/confidence/semantic/regime diversity"),
            ("concentration_risks_reduced", "repeated-pattern and regime-monoculture concentration"),
            ("saturation_or_repetition_flags", OrderedDict([("semantic_saturation_penalty", sat), ("repeated_pattern_penalty", rep)])),
            ("governance_readiness_status", "GOVERNANCE_READY" if gov_ready else "GOVERNANCE_INCOMPLETE"),
            ("lineage_refs", deepcopy(pool.get("governance_lineage_refs") or pool.get("lineage_refs") or [])),
            ("plan_eligibility_status", eligibility),
        ]))
    return sorted(out, key=lambda r: (str(r.get("candidate_id")), str(r.get("replay_window_ref"))))


def build_cd3_bounded_expansion_plan(*, candidate_set: Any, max_candidate_count: int = 5) -> OrderedDict[str, Any]:
    rows = _as_rows(deepcopy(candidate_set))
    max_count = max(1, int(max_candidate_count or 5))
    eligible = [r for r in rows if r.get("plan_eligibility_status") == ELIGIBLE_FOR_OPERATOR_REVIEW]
    deferred = [r for r in rows if r.get("plan_eligibility_status") != ELIGIBLE_FOR_OPERATOR_REVIEW]
    bucket_rank = {"HIGH_NOVELTY_REPLAY_PRIORITY": 0, "BALANCED_DIVERSIFICATION_PRIORITY": 1}
    selected = sorted(eligible, key=lambda r: (bucket_rank.get(str(r.get("priority_bucket")), 99), -_bounded((r.get("novelty_score_summary") or {}).get("marginal_structural_information_gain")), str(r.get("candidate_id"))))[:max_count]
    deferred_all = sorted(deferred + [r for r in eligible if r not in selected], key=lambda r: (str(r.get("plan_eligibility_status")), str(r.get("candidate_id"))))
    return OrderedDict([
        ("selected_candidates", selected),
        ("deferred_candidates", deferred_all),
        ("selection_policy", "Prioritize HIGH_NOVELTY_REPLAY_PRIORITY, include BALANCED_DIVERSIFICATION_PRIORITY for diversity balance, defer saturated/repetitive, governance-incomplete, insufficient-data, and low-marginal-information candidates with deterministic ordering and tie-breaks."),
        ("diversity_balance_summary", OrderedDict([("selected_count", len(selected)), ("balanced_diversification_included", any(r.get("priority_bucket") == "BALANCED_DIVERSIFICATION_PRIORITY" for r in selected))])),
        ("novelty_coverage_summary", OrderedDict([("high_novelty_selected", sum(1 for r in selected if r.get("priority_bucket") == "HIGH_NOVELTY_REPLAY_PRIORITY")), ("total_selected", len(selected))])),
        ("concentration_risk_reduction_summary", "Plan defers saturated/repetitive candidates and favors lower concentration-risk replay windows."),
        ("governance_preconditions", build_cd3_governance_preflight_checklist()),
        ("explicit_non_execution_notice", "CD3 is a deterministic, read-only replay expansion planning layer only. It does not execute replay, does not trigger D21, does not write data, and does not grant execution approval."),
    ])


def build_cd3_operator_review_queue(*, expansion_plan: Mapping[str, Any]) -> list[OrderedDict[str, Any]]:
    candidates = list(expansion_plan.get("selected_candidates") or []) + list(expansion_plan.get("deferred_candidates") or [])
    out = []
    for idx, row in enumerate(candidates, start=1):
        status = str(row.get("plan_eligibility_status"))
        action = "REVIEW_FOR_GOVERNED_REPLAY_APPROVAL"
        if status == DEFER_GOVERNANCE_INCOMPLETE:
            action = "DEFER_PENDING_GOVERNANCE_COMPLETION"
        elif status == DEFER_SATURATED_OR_REPETITIVE:
            action = "DEFER_DUE_TO_SATURATION"
        elif status == DEFER_LOW_MARGINAL_INFORMATION:
            action = "DEFER_DUE_TO_LOW_INFORMATION_GAIN"
        elif status == DEFER_INSUFFICIENT_DATA:
            action = "DEFER_PENDING_MORE_DATA"
        out.append(OrderedDict([
            ("review_rank", idx), ("candidate_id", row.get("candidate_id")), ("replay_window_ref", row.get("replay_window_ref")), ("priority_bucket", row.get("priority_bucket")),
            ("primary_novelty_reason", f"Marginal information gain={_bounded((row.get('novelty_score_summary') or {}).get('marginal_structural_information_gain'))}"),
            ("strengthened_dimensions", row.get("diversity_dimensions_strengthened")),
            ("risk_reduction_reason", row.get("concentration_risks_reduced")),
            ("governance_readiness_status", row.get("governance_readiness_status")),
            ("recommended_operator_action", action),
        ]))
    return out


def build_cd3_governance_preflight_checklist() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("d8_b4_d21_approval_still_required", True),
        ("non_dry_execution_approval_required_separately", True),
        ("append_only_persistence_must_remain_enabled", True),
        ("duplicate_prevention_must_remain_enabled", True),
        ("checksum_lineage_must_remain_enforced", True),
        ("bounded_replay_scope_must_be_confirmed", True),
        ("operator_approval_required", True),
        ("no_direct_sql", True),
        ("no_predictive_or_trading_interpretation", True),
        ("no_autonomous_execution", True),
    ])


def build_cd3_expansion_plan_rationale(*, expansion_plan: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("selected_candidate_rationale", "Selected candidates maximize novelty coverage first and include balanced diversification second under deterministic bounded selection."),
        ("deferred_candidate_rationale", "Deferred candidates are deterministically deferred for saturation/repetition, governance incompleteness, insufficient data, or low marginal information gain."),
        ("novelty_diversity_improvement", "The plan increases replay novelty coverage while preserving cross-dimension diversity balance."),
        ("concentration_risk_reduction", "The plan reduces concentration risk by deprioritizing repetitive and saturated candidate patterns."),
        ("not_execution_approval", "This plan is recommendation-only and does not authorize replay execution."),
        ("d21_approval_separation", "D21 approval remains an explicitly separate governance decision after operator review."),
    ])


def build_cd3_dashboard_payload(*, expansion_plan: Mapping[str, Any], operator_review_queue: Any, rationale: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("Governed Replay Expansion Plan Overview", OrderedDict([("selected_count", len(expansion_plan.get("selected_candidates") or [])), ("deferred_count", len(expansion_plan.get("deferred_candidates") or [])), ("plan_only", True), ("deterministic", True)])),
        ("Selected Replay Candidates", deepcopy(list(expansion_plan.get("selected_candidates") or []))),
        ("Deferred Replay Candidates", deepcopy(list(expansion_plan.get("deferred_candidates") or []))),
        ("Operator Review Queue", deepcopy(_as_rows(operator_review_queue))),
        ("Novelty Coverage Summary", deepcopy(dict(expansion_plan.get("novelty_coverage_summary") or {}))),
        ("Diversity Balance Summary", deepcopy(dict(expansion_plan.get("diversity_balance_summary") or {}))),
        ("Concentration Risk Reduction Summary", expansion_plan.get("concentration_risk_reduction_summary")),
        ("Governance Preflight Checklist", deepcopy(dict(expansion_plan.get("governance_preconditions") or {}))),
        ("Expansion Plan Rationale", deepcopy(dict(rationale or {}))),
        ("Explicit Non-Execution Notice", expansion_plan.get("explicit_non_execution_notice")),
    ])


def certify_cd3_governed_novelty_guided_replay_expansion_plan(*, candidate_set: Any, expansion_plan: Mapping[str, Any], dashboard_payload: Mapping[str, Any], operator_review_queue: Any) -> OrderedDict[str, Any]:
    rows = _as_rows(candidate_set)
    deterministic = [r.get("candidate_id") for r in rows] == sorted(r.get("candidate_id") for r in rows)
    bounded = len(expansion_plan.get("selected_candidates") or []) <= max(1, len(rows))
    checklist_present = bool((dashboard_payload or {}).get("Governance Preflight Checklist"))
    non_execution_present = bool((dashboard_payload or {}).get("Explicit Non-Execution Notice"))
    recommendation_only = all(str(r.get("recommended_operator_action", "")).startswith(("REVIEW_", "DEFER_")) for r in _as_rows(operator_review_queue))
    blocked = not (deterministic and checklist_present and non_execution_present and recommendation_only)
    degraded = not blocked and (not bounded or len(rows) == 0)
    status = BLOCKED_GOVERNED_NOVELTY_GUIDED_REPLAY_EXPANSION_PLAN if blocked else (DEGRADED_GOVERNED_NOVELTY_GUIDED_REPLAY_EXPANSION_PLAN if degraded else CERTIFIED_GOVERNED_NOVELTY_GUIDED_REPLAY_EXPANSION_PLAN)
    return OrderedDict([
        ("status", status),
        ("deterministic_candidate_ordering_preserved", deterministic),
        ("bounded_plan_size_preserved", bounded),
        ("no_replay_execution", True), ("no_d21_execution", True), ("no_writes", True), ("no_direct_sql", True),
        ("no_predictive_or_trading_behavior", True), ("no_autonomous_approval", True),
        ("governance_preflight_checklist_present", checklist_present), ("explicit_non_execution_notice_present", non_execution_present),
        ("recommendation_only_semantics_preserved", recommendation_only),
        ("checksum", _stable_checksum({"candidate_set": candidate_set, "expansion_plan": expansion_plan, "dashboard_payload": dashboard_payload})),
    ])


def build_cd3_report_payload(*, dashboard_payload: Mapping[str, Any], certification: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([("dashboard", deepcopy(dict(dashboard_payload))), ("certification", deepcopy(dict(certification)))])


def build_cd3_report_markdown(*, report_payload: Mapping[str, Any]) -> str:
    cert = dict((report_payload or {}).get("certification") or {})
    return "\n".join(["# CD3 Governed Novelty-Guided Replay Expansion Plan", f"- Status: {cert.get('status', 'UNKNOWN')}", "- Deterministic, bounded, operator-reviewable, plan-only replay expansion guidance."])


__all__ = [x for x in globals() if x.startswith("build_cd3_") or x.startswith("certify_cd3_") or x.endswith("GOVERNED_NOVELTY_GUIDED_REPLAY_EXPANSION_PLAN") or x.startswith("ELIGIBLE_") or x.startswith("DEFER_")]
