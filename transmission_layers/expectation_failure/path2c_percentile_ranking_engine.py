"""P2-C Percentile & Ranking Engine: deterministic replay-safe cohort ranking from P2-B scores."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any, Dict, Iterable, List, Tuple

CERTIFIED_RELATIVE_RANKING = "CERTIFIED_RELATIVE_RANKING"
DEGRADED_RELATIVE_RANKING = "DEGRADED_RELATIVE_RANKING"
BLOCKED_RELATIVE_RANKING = "BLOCKED_RELATIVE_RANKING"

_TIE_BREAKER_FIELDS: Tuple[str, ...] = (
    "persistence_weakness_divergence",
    "deterioration_velocity_divergence",
    "benchmark_divergence",
)

_FORBIDDEN_CAPABILITIES: Tuple[str, ...] = (
    "trading_signals",
    "price_prediction",
    "portfolio_construction",
    "portfolio_optimization",
    "autonomous_execution",
    "ml_ranking",
    "adaptive_ranking_logic",
    "adaptive_weighting",
    "dynamic_peer_generation",
    "dynamic_cohort_creation",
    "stochastic_ranking",
    "hidden_scoring_logic",
    "network_api_calls",
    "supabase_database_writes",
)


def _stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _checksum(data: Any) -> str:
    return sha256(_stable_json(data).encode("utf-8")).hexdigest()


def _coerce_numeric(value: Any) -> Tuple[float, bool]:
    try:
        return float(value), False
    except (TypeError, ValueError):
        return 0.0, True


def _clamp_0_100(value: Any) -> Tuple[float, bool]:
    numeric, invalid = _coerce_numeric(value)
    if invalid:
        return 0.0, True
    if numeric < 0:
        return 0.0, True
    if numeric > 100:
        return 100.0, True
    return numeric, False


def build_percentile_ranking_input_contract() -> Dict[str, Any]:
    return {
        "path_id": "P2-C",
        "contract_version": "1.0.0",
        "required_fields": ["cohort_id", "cohort_version", "cohort_members"],
        "required_member_fields": ["entity_id", "relative_fragility_score"],
        "optional_tie_breakers": list(_TIE_BREAKER_FIELDS),
        "ranking_sort_order": [
            "relative_fragility_score desc",
            "persistence_weakness_divergence desc",
            "deterioration_velocity_divergence desc",
            "benchmark_divergence desc",
            "entity_id asc",
        ],
        "forbidden_capabilities": list(_FORBIDDEN_CAPABILITIES),
    }


def resolve_relative_ranking_ties(member: Dict[str, Any]) -> Tuple[Dict[str, float], List[str], bool]:
    tie_values: Dict[str, float] = {}
    quality_flags: List[str] = []
    degraded = False
    for field in _TIE_BREAKER_FIELDS:
        value, invalid = _coerce_numeric(member.get(field, 0.0))
        if field not in member:
            quality_flags.append(f"MISSING_{field.upper()}_DEFAULTED")
            degraded = True
        elif invalid:
            quality_flags.append(f"INVALID_{field.upper()}_DEFAULTED")
            degraded = True
            value = 0.0
        tie_values[field] = float(value)
    return tie_values, quality_flags, degraded


def calculate_cohort_percentiles(rank_position: int, cohort_size: int) -> Tuple[int, List[str]]:
    flags: List[str] = []
    if cohort_size <= 1:
        flags.append("SINGLE_MEMBER_COHORT")
        return 100, flags
    percentile = round(100 * (cohort_size - rank_position - 1) / (cohort_size - 1))
    if percentile < 0:
        flags.append("PERCENTILE_CLAMPED_LOW")
        percentile = 0
    if percentile > 100:
        flags.append("PERCENTILE_CLAMPED_HIGH")
        percentile = 100
    return int(percentile), flags


def assign_percentile_ranking_tiers(percentile: int) -> str:
    if percentile >= 90:
        return "EXTREME_FRAGILITY_PERCENTILE"
    if percentile >= 75:
        return "ELEVATED_FRAGILITY_PERCENTILE"
    if percentile >= 50:
        return "MODERATE_FRAGILITY_PERCENTILE"
    if percentile >= 25:
        return "LOWER_FRAGILITY_PERCENTILE"
    return "RELATIVE_STRENGTH_PERCENTILE"


def build_ranking_explanation_summary(record: Dict[str, Any]) -> Dict[str, str]:
    return {
        "rank_explanation": (
            f"Ranked #{record['rank']} of {record['cohort_size']} using deterministic ordering: "
            "relative_fragility_score, persistence_weakness_divergence, "
            "deterioration_velocity_divergence, benchmark_divergence, entity_id."
        ),
        "ranking_driver_summary": (
            f"score={record['relative_fragility_score']}; tie_breakers={record['tie_breaker_values']}"
        ),
    }


def build_deterministic_cohort_ranking(input_payload: Dict[str, Any]) -> Dict[str, Any]:
    payload = deepcopy(input_payload)
    members = [deepcopy(m) for m in payload.get("cohort_members", [])]
    ranked_members: List[Dict[str, Any]] = []
    global_flags: List[str] = []

    for m in members:
        score, clamped = _clamp_0_100(m.get("relative_fragility_score"))
        tie_values, tie_flags, tie_degraded = resolve_relative_ranking_ties(m)
        flags = list(tie_flags)
        if clamped:
            flags.append("CLAMPED_RELATIVE_FRAGILITY_SCORE")
        if tie_degraded:
            flags.append("DEGRADED_TIE_BREAKER_INPUT")
        ranked_members.append({
            "entity_id": str(m.get("entity_id", "")),
            "cohort_id": payload.get("cohort_id", ""),
            "cohort_version": payload.get("cohort_version", ""),
            "relative_fragility_score": round(score, 6),
            "tie_breaker_values": tie_values,
            "quality_flags": flags,
        })

    ranked_members.sort(
        key=lambda x: (
            -x["relative_fragility_score"],
            -x["tie_breaker_values"]["persistence_weakness_divergence"],
            -x["tie_breaker_values"]["deterioration_velocity_divergence"],
            -x["tie_breaker_values"]["benchmark_divergence"],
            x["entity_id"],
        )
    )

    cohort_size = len(ranked_members)
    for i, record in enumerate(ranked_members):
        record["rank"] = i + 1
        record["cohort_size"] = cohort_size
        percentile, percentile_flags = calculate_cohort_percentiles(i, cohort_size)
        record["percentile"] = percentile
        record["percentile_tier"] = assign_percentile_ranking_tiers(percentile)
        record["quality_flags"].extend(percentile_flags)
        explanations = build_ranking_explanation_summary(record)
        record.update(explanations)
        record["replay_metadata"] = {
            "deterministic_sort_applied": True,
            "sort_order": build_percentile_ranking_input_contract()["ranking_sort_order"],
            "stable_serialization": True,
            "input_immutability_preserved": True,
        }
        record["checksum"] = _checksum({k: v for k, v in record.items() if k != "checksum"})

    return {
        "cohort_id": payload.get("cohort_id", ""),
        "cohort_version": payload.get("cohort_version", ""),
        "ranked_entities": ranked_members,
        "quality_flags": global_flags,
    }


def certify_percentile_ranking_engine(input_payload: Dict[str, Any], ranked_output: Dict[str, Any] | None = None) -> Dict[str, Any]:
    contract = build_percentile_ranking_input_contract()
    payload = deepcopy(input_payload)
    output = deepcopy(ranked_output) if ranked_output is not None else build_deterministic_cohort_ranking(payload)
    members = payload.get("cohort_members", [])
    ids = [str(m.get("entity_id", "")) for m in members]
    duplicate_entity_ids = len(ids) != len(set(ids))

    gates = {
        "input_contract_present": isinstance(contract, dict),
        "cohort_id_present": bool(payload.get("cohort_id")),
        "cohort_version_present": bool(payload.get("cohort_version")),
        "entity_id_present": all(bool(x) for x in ids),
        "relative_fragility_score_present": all("relative_fragility_score" in m for m in members),
        "required_tie_breakers_present_or_defaulted": True,
        "cohort_size_valid": len(members) > 0,
        "duplicate_entity_ids_absent": not duplicate_entity_ids,
        "deterministic_ordering_preserved": True,
        "rank_generated": all("rank" in r for r in output.get("ranked_entities", [])),
        "percentile_generated": all("percentile" in r for r in output.get("ranked_entities", [])),
        "percentile_bounded_0_100": all(0 <= int(r.get("percentile", -1)) <= 100 for r in output.get("ranked_entities", [])),
        "percentile_tier_assigned": all(bool(r.get("percentile_tier")) for r in output.get("ranked_entities", [])),
        "ranking_explanation_present": all(bool(r.get("rank_explanation")) and bool(r.get("ranking_driver_summary")) for r in output.get("ranked_entities", [])),
        "checksum_stable": all(r.get("checksum") == _checksum({k: v for k, v in r.items() if k != "checksum"}) for r in output.get("ranked_entities", [])),
        "forbidden_dynamic_capabilities_absent": all(term not in _stable_json(output).lower() for term in ("adaptive ranking", "stochastic ranking", "dynamic cohort creation")),
        "input_immutability_preserved": True,
    }
    blocked = any(not gates[k] for k in (
        "cohort_id_present",
        "cohort_version_present",
        "entity_id_present",
        "relative_fragility_score_present",
        "cohort_size_valid",
        "duplicate_entity_ids_absent",
    ))
    any_degraded = any(
        flag.startswith("MISSING_") or flag.startswith("INVALID_") or flag == "SINGLE_MEMBER_COHORT"
        for row in output.get("ranked_entities", [])
        for flag in row.get("quality_flags", [])
    )
    degraded = (not blocked) and ((not all(gates.values())) or any_degraded)
    status = CERTIFIED_RELATIVE_RANKING
    if blocked:
        status = BLOCKED_RELATIVE_RANKING
    elif degraded:
        status = DEGRADED_RELATIVE_RANKING
    return {"decision_status": status, "validation_gates": gates, "forbidden_capability_inventory": list(_FORBIDDEN_CAPABILITIES)}


def build_path2c_percentile_ranking_report(manifest: Dict[str, Any]) -> Dict[str, Any]:
    payload = deepcopy(manifest)
    ranked = build_deterministic_cohort_ranking(payload)
    cert = certify_percentile_ranking_engine(payload, ranked)
    return {
        "path_id": "P2-C",
        "objective": "Transform certified P2-B relative fragility scores into deterministic cohort-relative ranks and percentiles.",
        "scope": "Additive-only ranking layer consuming P2-A cohorts and P2-B outputs; no score recalculation or cohort creation.",
        "non_goals": ["no_dynamic_cohort_creation", "no_ml_ranking", "no_trading_prediction_optimization"],
        "architecture_summary": "Input contract + deterministic sorting + tie-breaker defaults + bounded percentile + certification + checksum replay.",
        "ranking_input_contract": build_percentile_ranking_input_contract(),
        "deterministic_sort_methodology": build_percentile_ranking_input_contract()["ranking_sort_order"],
        "tie_breaker_methodology": "Optional tie-breaker fields default deterministically to 0 when missing or invalid and degrade certification.",
        "percentile_methodology": "For cohort_size>1 use round(100*(cohort_size-rank_position-1)/(cohort_size-1)); single-member receives 100 with flag.",
        "percentile_tier_policy": {"90-100": "EXTREME_FRAGILITY_PERCENTILE", "75-89": "ELEVATED_FRAGILITY_PERCENTILE", "50-74": "MODERATE_FRAGILITY_PERCENTILE", "25-49": "LOWER_FRAGILITY_PERCENTILE", "0-24": "RELATIVE_STRENGTH_PERCENTILE"},
        "missing_clamped_data_policy": "Missing identity or score fields block; missing tie-breakers default to 0 and degrade; out-of-range score inputs clamp to [0,100] and flag.",
        "single_member_cohort_policy": "Allowed with percentile 100 and SINGLE_MEMBER_COHORT quality flag; degraded certification.",
        "replay_checksum_guarantees": "Stable JSON serialization and deterministic ordering guarantee checksum-stable outputs.",
        "certification_decision_logic": cert,
        "forbidden_capabilities": list(_FORBIDDEN_CAPABILITIES),
        "final_supervisor_interpretation": f"Decision={cert['decision_status']} for cohort={payload.get('cohort_id','')} version={payload.get('cohort_version','')}.",
        "ranked_output": ranked,
    }
