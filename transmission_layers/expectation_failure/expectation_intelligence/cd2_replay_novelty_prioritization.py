"""CD2 Replay Novelty Prioritization (deterministic, read-only, recommendation-only)."""

from __future__ import annotations

from collections import Counter, OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

CERTIFIED_REPLAY_NOVELTY_PRIORITIZATION = "CERTIFIED_REPLAY_NOVELTY_PRIORITIZATION"
DEGRADED_REPLAY_NOVELTY_PRIORITIZATION = "DEGRADED_REPLAY_NOVELTY_PRIORITIZATION"
BLOCKED_REPLAY_NOVELTY_PRIORITIZATION = "BLOCKED_REPLAY_NOVELTY_PRIORITIZATION"

CD2_PRIORITY_BUCKETS = (
    "HIGH_NOVELTY_REPLAY_PRIORITY",
    "BALANCED_DIVERSIFICATION_PRIORITY",
    "LOW_MARGINAL_INFORMATION_PRIORITY",
    "SATURATED_OR_REPETITIVE_CANDIDATE",
    "GOVERNANCE_INCOMPLETE_CANDIDATE",
    "INSUFFICIENT_DATA_CANDIDATE",
)


def _stable_checksum(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _as_rows(rows: Any) -> list[dict[str, Any]]:
    if isinstance(rows, Mapping):
        return [dict(rows)]
    return [dict(r) for r in list(rows or []) if isinstance(r, Mapping)]


def _as_token(value: Any, default: str = "unknown") -> str:
    text = str(value or "").strip().lower()
    return text if text else default


def _bounded(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, round(float(value), 6)))


def build_cd2_replay_candidate_pool(*, replay_windows: Any, cd1_dashboard_payload: Mapping[str, Any] | None = None, h3_dashboard_payload: Mapping[str, Any] | None = None) -> list[OrderedDict[str, Any]]:
    rows = _as_rows(deepcopy(replay_windows))
    out: list[OrderedDict[str, Any]] = []
    for idx, row in enumerate(rows):
        candidate_id = str(row.get("candidate_id") or row.get("replay_id") or row.get("record_id") or f"candidate_{idx:04d}")
        out.append(OrderedDict([
            ("candidate_id", candidate_id),
            ("replay_window_ref", row.get("replay_window_ref") or row.get("window_ref") or row.get("run_id") or candidate_id),
            ("source_offsets", deepcopy(row.get("source_offsets") or row.get("offsets") or [])),
            ("regime_state", _as_token(row.get("regime_state") or row.get("regime") or row.get("regime_label"))),
            ("contradiction_state", _as_token(row.get("contradiction_state") or row.get("contradiction_label"))),
            ("continuity_state", _as_token(row.get("continuity_state"))),
            ("confidence_state", _as_token(row.get("confidence_state") or row.get("confidence_label"))),
            ("semantic_theme_family", _as_token(row.get("semantic_theme_family") or row.get("semantic_themes") or row.get("themes"))),
            ("pattern_family", _as_token(row.get("pattern_family"), "unclassified")),
            ("prior_recurrence_count", int(row.get("prior_recurrence_count") or row.get("recurrence_count") or 0)),
            ("transition_signature", _as_token(row.get("transition_signature") or row.get("transition_id"))),
            ("governance_lineage_refs", deepcopy(row.get("governance_lineage_refs") or row.get("lineage_refs") or [])),
        ]))
    return sorted(out, key=lambda x: (str(x.get("candidate_id")), str(x.get("replay_window_ref"))))


def build_cd2_novelty_scorecard(*, candidate_pool: list[Mapping[str, Any]]) -> list[OrderedDict[str, Any]]:
    rows = [OrderedDict(r) for r in _as_rows(deepcopy(candidate_pool))]
    regime_counts = Counter(_as_token(r.get("regime_state")) for r in rows)
    contradiction_counts = Counter(_as_token(r.get("contradiction_state")) for r in rows)
    continuity_counts = Counter(_as_token(r.get("continuity_state")) for r in rows)
    confidence_counts = Counter(_as_token(r.get("confidence_state")) for r in rows)
    semantic_counts = Counter(_as_token(r.get("semantic_theme_family")) for r in rows)
    pattern_counts = Counter(_as_token(r.get("pattern_family"), "unclassified") for r in rows)
    transition_counts = Counter(_as_token(r.get("transition_signature")) for r in rows)

    scorecard: list[OrderedDict[str, Any]] = []
    for r in rows:
        recur = max(0, int(r.get("prior_recurrence_count") or 0))
        gov_ready = bool(r.get("governance_lineage_refs"))
        miss = sum(1 for k in ("regime_state", "contradiction_state", "continuity_state", "confidence_state", "semantic_theme_family", "transition_signature") if _as_token(r.get(k)) == "unknown")
        contradiction_novelty = 1 / contradiction_counts[_as_token(r.get("contradiction_state"))]
        continuity_novelty = 1 / continuity_counts[_as_token(r.get("continuity_state"))]
        confidence_novelty = 1 / confidence_counts[_as_token(r.get("confidence_state"))]
        semantic_novelty = 1 / semantic_counts[_as_token(r.get("semantic_theme_family"))]
        regime_novelty = 1 / regime_counts[_as_token(r.get("regime_state"))]
        signature_rarity = 1 / transition_counts[_as_token(r.get("transition_signature"))]
        saturation_penalty = _bounded((semantic_counts[_as_token(r.get("semantic_theme_family"))] - 1) / max(len(rows), 1))
        repeated_penalty = _bounded((pattern_counts[_as_token(r.get("pattern_family"), "unclassified")] - 1 + recur) / max(len(rows) + 3, 1))
        monoculture_penalty = _bounded((regime_counts[_as_token(r.get("regime_state"))] - 1) / max(len(rows), 1))
        gain = _bounded((contradiction_novelty + continuity_novelty + confidence_novelty + semantic_novelty + regime_novelty + signature_rarity) / 6 - (saturation_penalty + repeated_penalty + monoculture_penalty) / 3)
        scorecard.append(OrderedDict([
            ("candidate_id", r.get("candidate_id")),
            ("contradiction_type_novelty", _bounded(contradiction_novelty)),
            ("continuity_transition_novelty", _bounded(continuity_novelty)),
            ("confidence_transition_novelty", _bounded(confidence_novelty)),
            ("semantic_theme_novelty", _bounded(semantic_novelty)),
            ("regime_transition_novelty", _bounded(regime_novelty)),
            ("transition_signature_rarity", _bounded(signature_rarity)),
            ("marginal_structural_information_gain", gain),
            ("semantic_saturation_penalty", saturation_penalty),
            ("repeated_pattern_penalty", repeated_penalty),
            ("regime_monoculture_penalty", monoculture_penalty),
            ("governance_readiness_modifier", 1.0 if gov_ready else 0.25),
            ("missing_dimension_count", miss),
        ]))
    return sorted(scorecard, key=lambda x: str(x.get("candidate_id")))


def build_cd2_candidate_priority_buckets(*, candidate_pool: list[Mapping[str, Any]], novelty_scorecard: list[Mapping[str, Any]]) -> OrderedDict[str, list[str]]:
    score_by_id = {str(r.get("candidate_id")): dict(r) for r in _as_rows(novelty_scorecard)}
    buckets: OrderedDict[str, list[str]] = OrderedDict((b, []) for b in CD2_PRIORITY_BUCKETS)
    for row in _as_rows(candidate_pool):
        cid = str(row.get("candidate_id"))
        s = score_by_id.get(cid, {})
        if int(s.get("missing_dimension_count", 99)) >= 4:
            bucket = "INSUFFICIENT_DATA_CANDIDATE"
        elif float(s.get("governance_readiness_modifier", 0.0)) < 1.0:
            bucket = "GOVERNANCE_INCOMPLETE_CANDIDATE"
        elif float(s.get("semantic_saturation_penalty", 1.0)) >= 0.6 or float(s.get("repeated_pattern_penalty", 1.0)) >= 0.6:
            bucket = "SATURATED_OR_REPETITIVE_CANDIDATE"
        elif float(s.get("marginal_structural_information_gain", 0.0)) >= 0.65:
            bucket = "HIGH_NOVELTY_REPLAY_PRIORITY"
        elif float(s.get("marginal_structural_information_gain", 0.0)) <= 0.25:
            bucket = "LOW_MARGINAL_INFORMATION_PRIORITY"
        else:
            bucket = "BALANCED_DIVERSIFICATION_PRIORITY"
        buckets[bucket].append(cid)
    for key in buckets:
        buckets[key] = sorted(set(buckets[key]))
    return buckets


def build_cd2_replay_selection_rationale(*, candidate_pool: list[Mapping[str, Any]], novelty_scorecard: list[Mapping[str, Any]], priority_buckets: Mapping[str, Any]) -> list[OrderedDict[str, Any]]:
    score_by_id = {str(r.get("candidate_id")): dict(r) for r in _as_rows(novelty_scorecard)}
    bucket_of: dict[str, str] = {}
    for bucket, ids in dict(priority_buckets or {}).items():
        for cid in ids or []:
            bucket_of[str(cid)] = str(bucket)
    out = []
    for row in _as_rows(candidate_pool):
        cid = str(row.get("candidate_id"))
        s = score_by_id.get(cid, {})
        out.append(OrderedDict([
            ("candidate_id", cid),
            ("bucket", bucket_of.get(cid, "INSUFFICIENT_DATA_CANDIDATE")),
            ("novelty_usefulness", f"Structural novelty gain={_bounded(s.get('marginal_structural_information_gain', 0.0))} with transition rarity={_bounded(s.get('transition_signature_rarity', 0.0))}."),
            ("diversity_dimension_strengthened", "contradiction/continuity/confidence/semantic/regime diversity"),
            ("concentration_risk_effect", f"Reduces concentration when repeated_pattern_penalty={_bounded(s.get('repeated_pattern_penalty', 0.0))} and regime_monoculture_penalty={_bounded(s.get('regime_monoculture_penalty', 0.0))} stay low."),
            ("recommendation_only_notice", "CD2 is recommendation-only for operator review and does not execute replay."),
            ("execution_approval_notice", "Priority assignment does not imply D21 approval or execution authorization."),
        ]))
    return sorted(out, key=lambda x: str(x.get("candidate_id")))


def build_cd2_prioritization_summary(*, candidate_pool: list[Mapping[str, Any]], novelty_scorecard: list[Mapping[str, Any]], priority_buckets: Mapping[str, Any]) -> OrderedDict[str, Any]:
    scores = _as_rows(novelty_scorecard)
    by = {str(s.get("candidate_id")): s for s in scores}
    ranked = sorted(scores, key=lambda s: (-float(s.get("marginal_structural_information_gain", 0.0)), str(s.get("candidate_id"))))
    def top(metric: str, n: int = 3) -> list[str]:
        return [str(r.get("candidate_id")) for r in sorted(scores, key=lambda s: (-float(s.get(metric, 0.0)), str(s.get("candidate_id"))))[:n]]
    weak = [str(r.get("candidate_id")) for r in sorted(scores, key=lambda s: (float(s.get("marginal_structural_information_gain", 0.0)), -float(s.get("semantic_saturation_penalty", 0.0)), str(s.get("candidate_id"))))[:3]]
    defer = sorted(set((priority_buckets or {}).get("SATURATED_OR_REPETITIVE_CANDIDATE", []) + (priority_buckets or {}).get("GOVERNANCE_INCOMPLETE_CANDIDATE", [])))
    return OrderedDict([
        ("strongest_novelty_candidates", [str(r.get("candidate_id")) for r in ranked[:5]]),
        ("weakest_or_repetitive_candidates", weak),
        ("best_regime_diversification_candidates", top("regime_transition_novelty")),
        ("best_contradiction_diversification_candidates", top("contradiction_type_novelty")),
        ("best_continuity_transition_candidates", top("continuity_transition_novelty")),
        ("best_confidence_transition_candidates", top("confidence_transition_novelty")),
        ("best_semantic_theme_novelty_candidates", top("semantic_theme_novelty")),
        ("candidates_to_defer", defer),
        ("candidate_count", len(by)),
    ])


def build_cd2_operator_guardrails() -> OrderedDict[str, Any]:
    return OrderedDict([("no_autonomous_execution", True), ("no_d21_execution", True), ("no_writes", True), ("no_direct_sql", True), ("no_predictive_or_trading_interpretation", True), ("operator_approval_required_for_governed_replay_expansion", True), ("preserves_append_only_replay_semantics", True), ("preserves_checksum_lineage", True), ("preserves_duplicate_prevention", True)])


def build_cd2_dashboard_payload(*, candidate_pool: list[Mapping[str, Any]], novelty_scorecard: list[Mapping[str, Any]], priority_buckets: Mapping[str, Any], selection_rationale: list[Mapping[str, Any]], prioritization_summary: Mapping[str, Any], operator_guardrails: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("Replay Novelty Prioritization Overview", OrderedDict([("candidate_count", len(candidate_pool)), ("recommendation_only", True), ("deterministic", True)])),
        ("Candidate Pool Summary", deepcopy(candidate_pool)),
        ("Novelty Scorecard", deepcopy(novelty_scorecard)),
        ("Priority Buckets", deepcopy(dict(priority_buckets))),
        ("Selection Rationale", deepcopy(selection_rationale)),
        ("Diversification Summary", deepcopy(dict(prioritization_summary))),
        ("Saturation/Repetition Warnings", OrderedDict([("saturated_or_repetitive_candidates", list((priority_buckets or {}).get("SATURATED_OR_REPETITIVE_CANDIDATE", []))), ("low_marginal_information_candidates", list((priority_buckets or {}).get("LOW_MARGINAL_INFORMATION_PRIORITY", [])))])),
        ("Governance/Operator Guardrails", deepcopy(dict(operator_guardrails))),
        ("Recommended Operator Review Queue", list((prioritization_summary or {}).get("strongest_novelty_candidates", []))),
    ])


def certify_cd2_replay_novelty_prioritization(*, candidate_pool: list[Mapping[str, Any]], novelty_scorecard: list[Mapping[str, Any]], dashboard_payload: Mapping[str, Any], operator_guardrails: Mapping[str, Any]) -> OrderedDict[str, Any]:
    guards = dict(operator_guardrails or {})
    deterministic = [str(r.get("candidate_id")) for r in _as_rows(candidate_pool)] == sorted(str(r.get("candidate_id")) for r in _as_rows(candidate_pool))
    bounded = all(0.0 <= float(v) <= 1.0 for row in _as_rows(novelty_scorecard) for k, v in row.items() if k.endswith(("novelty", "rarity", "gain", "penalty", "modifier")))
    guard_ok = all(bool(guards.get(k)) for k in ("no_autonomous_execution", "no_d21_execution", "no_writes", "no_direct_sql", "no_predictive_or_trading_interpretation"))
    if not deterministic or not guard_ok:
        status = BLOCKED_REPLAY_NOVELTY_PRIORITIZATION
    elif not bounded or len(_as_rows(candidate_pool)) < 2:
        status = DEGRADED_REPLAY_NOVELTY_PRIORITIZATION
    else:
        status = CERTIFIED_REPLAY_NOVELTY_PRIORITIZATION
    return OrderedDict([("status", status), ("deterministic_candidate_ordering_preserved", deterministic), ("bounded_scorecard_preserved", bounded), ("recommendation_only", True), ("checksum", _stable_checksum({"pool": candidate_pool, "scorecard": novelty_scorecard, "dashboard": dashboard_payload}))])


def build_cd2_report_payload(*, dashboard_payload: Mapping[str, Any], certification: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([("dashboard", deepcopy(dict(dashboard_payload))), ("certification", deepcopy(dict(certification)))])


def build_cd2_report_markdown(*, report_payload: Mapping[str, Any]) -> str:
    cert = dict((report_payload or {}).get("certification") or {})
    return "\n".join(["# CD2 Replay Novelty Prioritization", f"- Status: {cert.get('status', 'UNKNOWN')}", "- Deterministic, recommendation-only replay prioritization for operator review."])


__all__ = [x for x in globals() if x.startswith("build_cd2_") or x.startswith("certify_cd2_") or x.endswith("REPLAY_NOVELTY_PRIORITIZATION") or x == "CD2_PRIORITY_BUCKETS"]
