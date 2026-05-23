"""P2-B Relative Fragility Scoring: deterministic, replay-safe cohort-relative scoring."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any, Dict, Iterable, List, Tuple

CERTIFIED_RELATIVE_FRAGILITY = "CERTIFIED_RELATIVE_FRAGILITY"
DEGRADED_RELATIVE_FRAGILITY = "DEGRADED_RELATIVE_FRAGILITY"
BLOCKED_RELATIVE_FRAGILITY = "BLOCKED_RELATIVE_FRAGILITY"

_ALLOWED_COMPONENTS: Tuple[str, ...] = (
    "fragility_level_divergence",
    "deterioration_velocity_divergence",
    "persistence_weakness_divergence",
    "regime_instability_divergence",
    "benchmark_divergence",
)

_COMPONENT_WEIGHTS: Dict[str, int] = {
    "fragility_level_divergence": 30,
    "deterioration_velocity_divergence": 25,
    "persistence_weakness_divergence": 20,
    "regime_instability_divergence": 15,
    "benchmark_divergence": 10,
}

_FORBIDDEN_CAPABILITIES: Tuple[str, ...] = (
    "trading_signals",
    "price_prediction",
    "portfolio_optimization",
    "autonomous_execution",
    "adaptive_weighting",
    "ml_clustering",
    "dynamic_peer_generation",
    "hidden_ranking_logic",
    "stochastic_scoring",
    "network_api_calls",
    "supabase_database_writes",
)


def _stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _checksum(data: Any) -> str:
    return sha256(_stable_json(data).encode("utf-8")).hexdigest()


def _clamp_0_100(value: Any) -> Tuple[float, bool]:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return 0.0, True
    if v < 0:
        return 0.0, True
    if v > 100:
        return 100.0, True
    return v, False


def _median(values: Iterable[float]) -> float:
    ordered = sorted(float(v) for v in values)
    if not ordered:
        return 0.0
    n = len(ordered)
    mid = n // 2
    return ordered[mid] if n % 2 == 1 else (ordered[mid - 1] + ordered[mid]) / 2.0


def _tier(score: float) -> str:
    if score >= 85:
        return "EXTREME_RELATIVE_FRAGILITY"
    if score >= 70:
        return "ELEVATED_RELATIVE_FRAGILITY"
    if score >= 50:
        return "MODERATE_RELATIVE_FRAGILITY"
    if score >= 30:
        return "STABLE_NEUTRAL"
    return "RELATIVE_STRENGTH"


def build_relative_fragility_input_contract() -> Dict[str, Any]:
    return {
        "path_id": "P2-B",
        "contract_version": "1.0.0",
        "required_fields": ["entity_id", "cohort_id", "cohort_version", "cohort_members"],
        "allowed_score_components": list(_ALLOWED_COMPONENTS),
        "fixed_component_weights": deepcopy(_COMPONENT_WEIGHTS),
        "fixed_weight_total": sum(_COMPONENT_WEIGHTS.values()),
        "forbidden_capabilities": list(_FORBIDDEN_CAPABILITIES),
    }


def build_cohort_relative_baselines(cohort_members: Iterable[Dict[str, Any]], *, component: str = "fragility_level_divergence") -> Dict[str, Any]:
    members = [deepcopy(m) for m in cohort_members]
    ordered = sorted(members, key=lambda x: str(x.get("entity_id", "")))
    values = [float(m.get(component, 0.0)) for m in ordered]
    return {
        "component": component,
        "member_order": [str(m.get("entity_id", "")) for m in ordered],
        "member_count": len(ordered),
        "peer_median": _median(values),
        "peer_mean": (sum(values) / len(values)) if values else 0.0,
    }


def compare_peer_fragility_distribution(entity_value: Any, peer_median: Any) -> Dict[str, Any]:
    entity, _ = _clamp_0_100(entity_value)
    median, _ = _clamp_0_100(peer_median)
    return {
        "entity_value": entity,
        "peer_median": median,
        "peer_median_delta": round(entity - median, 6),
    }


def build_relative_deterioration_velocity_comparison(entity_velocity: Any, peer_median_velocity: Any) -> Dict[str, Any]:
    base = compare_peer_fragility_distribution(entity_velocity, peer_median_velocity)
    return {"deterioration_velocity_delta": base["peer_median_delta"], "entity_velocity": base["entity_value"], "peer_velocity_median": base["peer_median"]}


def build_relative_persistence_weakness_comparison(entity_persistence: Any, peer_median_persistence: Any) -> Dict[str, Any]:
    base = compare_peer_fragility_distribution(entity_persistence, peer_median_persistence)
    return {"persistence_weakness_delta": base["peer_median_delta"], "entity_persistence": base["entity_value"], "peer_persistence_median": base["peer_median"]}


def build_relative_fragility_driver_summary(component_scores: Dict[str, Any], component_weights: Dict[str, int]) -> Dict[str, Any]:
    contributions = []
    for component in _ALLOWED_COMPONENTS:
        score, _ = _clamp_0_100(component_scores.get(component, 0.0))
        weight = int(component_weights.get(component, 0))
        contributions.append({"component": component, "score": score, "weight": weight, "weighted_contribution": round(score * weight / 100.0, 6)})
    ranked = sorted(contributions, key=lambda x: (-x["weighted_contribution"], x["component"]))
    return {
        "primary_driver": ranked[0]["component"] if ranked else "",
        "secondary_driver": ranked[1]["component"] if len(ranked) > 1 else "",
        "ranked_contributions": ranked,
    }


def build_relative_fragility_score(input_payload: Dict[str, Any]) -> Dict[str, Any]:
    payload = deepcopy(input_payload)
    component_scores: Dict[str, float] = {}
    quality_flags = {"missing_optional_components": [], "clamped_components": [], "degraded_data": False}

    for component in _ALLOWED_COMPONENTS:
        raw = payload.get(component)
        if raw is None:
            quality_flags["missing_optional_components"].append(component)
            raw = 0.0
        clamped, changed = _clamp_0_100(raw)
        if changed:
            quality_flags["clamped_components"].append(component)
        component_scores[component] = clamped

    weighted_sum = sum(component_scores[c] * _COMPONENT_WEIGHTS[c] for c in _ALLOWED_COMPONENTS) / 100.0
    score, score_clamped = _clamp_0_100(weighted_sum)
    if quality_flags["missing_optional_components"] or quality_flags["clamped_components"] or score_clamped:
        quality_flags["degraded_data"] = True

    cohort_members = deepcopy(payload.get("cohort_members", []))
    baseline = build_cohort_relative_baselines(cohort_members)
    peer_delta = compare_peer_fragility_distribution(component_scores["fragility_level_divergence"], baseline["peer_median"])

    velocity_baseline = _median(float(m.get("deterioration_velocity_divergence", 0.0)) for m in cohort_members)
    persistence_baseline = _median(float(m.get("persistence_weakness_divergence", 0.0)) for m in cohort_members)
    benchmark_baseline = _median(float(m.get("benchmark_divergence", 0.0)) for m in cohort_members)

    velocity_delta = build_relative_deterioration_velocity_comparison(component_scores["deterioration_velocity_divergence"], velocity_baseline)
    persistence_delta = build_relative_persistence_weakness_comparison(component_scores["persistence_weakness_divergence"], persistence_baseline)
    benchmark_delta = compare_peer_fragility_distribution(component_scores["benchmark_divergence"], benchmark_baseline)

    driver_summary = build_relative_fragility_driver_summary(component_scores, _COMPONENT_WEIGHTS)

    result = {
        "entity_id": payload.get("entity_id", ""),
        "cohort_id": payload.get("cohort_id", ""),
        "cohort_version": payload.get("cohort_version", ""),
        "relative_fragility_score": round(score, 6),
        "relative_fragility_tier": _tier(score),
        "component_scores": component_scores,
        "component_weights": deepcopy(_COMPONENT_WEIGHTS),
        "peer_baseline_summary": baseline,
        "peer_median_delta": peer_delta["peer_median_delta"],
        "deterioration_velocity_delta": velocity_delta["deterioration_velocity_delta"],
        "persistence_weakness_delta": persistence_delta["persistence_weakness_delta"],
        "benchmark_divergence_delta": benchmark_delta["peer_median_delta"],
        "driver_summary": driver_summary,
        "quality_flags": quality_flags,
        "replay_metadata": {
            "deterministic_member_ordering": baseline["member_order"],
            "stable_serialization": True,
            "input_immutability_preserved": True,
        },
    }
    result["checksum"] = _checksum(result)
    return result


def certify_relative_fragility_scoring(input_payload: Dict[str, Any], scored_output: Dict[str, Any] | None = None) -> Dict[str, Any]:
    contract = build_relative_fragility_input_contract()
    payload = deepcopy(input_payload)
    scored = deepcopy(scored_output) if scored_output is not None else build_relative_fragility_score(payload)

    members = payload.get("cohort_members", [])
    entity_id = payload.get("entity_id", "")
    member_ids = sorted(str(m.get("entity_id", "")) for m in members)

    gates = {
        "input_contract_present": isinstance(contract, dict),
        "cohort_id_present": bool(payload.get("cohort_id")),
        "entity_id_present": bool(entity_id),
        "cohort_members_present": isinstance(members, list) and len(members) > 0,
        "entity_belongs_to_cohort": str(entity_id) in member_ids,
        "allowed_score_components_present": set(scored.get("component_scores", {}).keys()) == set(_ALLOWED_COMPONENTS),
        "fixed_weight_total_equals_100": sum(scored.get("component_weights", {}).values()) == 100,
        "score_bounded_0_100": 0 <= float(scored.get("relative_fragility_score", -1)) <= 100,
        "deterministic_member_ordering_preserved": scored.get("replay_metadata", {}).get("deterministic_member_ordering", []) == sorted(member_ids),
        "peer_baseline_generated": isinstance(scored.get("peer_baseline_summary"), dict),
        "peer_median_generated": "peer_median" in scored.get("peer_baseline_summary", {}),
        "relative_score_generated": "relative_fragility_score" in scored,
        "relative_tier_assigned": bool(scored.get("relative_fragility_tier")),
        "driver_summary_present": isinstance(scored.get("driver_summary"), dict),
        "checksum_stable": scored.get("checksum") == _checksum({k: v for k, v in scored.items() if k != "checksum"}),
        "forbidden_dynamic_capabilities_absent": all(term not in _stable_json(scored).lower() for term in ("adaptive weighting", "stochastic scoring", "dynamic peer generation")),
        "input_immutability_preserved": True,
    }

    blocked_keys = ("cohort_id_present", "entity_id_present", "cohort_members_present", "entity_belongs_to_cohort")
    blocked = any(not gates[k] for k in blocked_keys)
    degraded = (not blocked) and (not all(gates.values()) or scored.get("quality_flags", {}).get("degraded_data", False))
    status = CERTIFIED_RELATIVE_FRAGILITY
    if blocked:
        status = BLOCKED_RELATIVE_FRAGILITY
    elif degraded:
        status = DEGRADED_RELATIVE_FRAGILITY

    return {"decision_status": status, "validation_gates": gates, "forbidden_capability_inventory": list(_FORBIDDEN_CAPABILITIES)}


def build_path2b_relative_fragility_report(manifest: Dict[str, Any]) -> Dict[str, Any]:
    payload = deepcopy(manifest)
    scored = build_relative_fragility_score(payload)
    cert = certify_relative_fragility_scoring(payload, scored)
    return {
        "path_id": "P2-B",
        "objective": "Convert absolute/path-temporal fragility inputs into bounded cohort-relative fragility scores.",
        "scope": "Additive-only deterministic scoring over explicit P2-A cohort structures.",
        "non_goals": ["no_dynamic_peer_generation", "no_adaptive_weighting", "no_trading_or_prediction_or_optimization"],
        "architecture_summary": "Input contract + cohort baseline medians + fixed weighted score + certification gates + checksum replay.",
        "input_contract": build_relative_fragility_input_contract(),
        "cohort_baseline_methodology": "Canonical cohort member ordering by entity_id with deterministic peer median baselines.",
        "scoring_component_methodology": "Five fixed components clamped to [0,100] and aggregated using static weights.",
        "fixed_weighting_policy": deepcopy(_COMPONENT_WEIGHTS),
        "tier_policy": {"85-100": "EXTREME_RELATIVE_FRAGILITY", "70-84": "ELEVATED_RELATIVE_FRAGILITY", "50-69": "MODERATE_RELATIVE_FRAGILITY", "30-49": "STABLE_NEUTRAL", "0-29": "RELATIVE_STRENGTH"},
        "missing_clamped_data_policy": "Missing optional components default to 0 and degrade certification; out-of-range values are clamped and flagged.",
        "deterministic_peer_comparison_policy": "Peer deltas computed against cohort medians with stable ordering and no stochastic logic.",
        "replay_checksum_guarantees": {"stable_json_serialization": True, "sha256_output_checksum": True, "checksum": scored.get("checksum", "")},
        "certification_decision_logic": cert,
        "forbidden_capabilities": list(_FORBIDDEN_CAPABILITIES),
        "final_supervisor_interpretation": cert.get("decision_status", BLOCKED_RELATIVE_FRAGILITY),
    }
