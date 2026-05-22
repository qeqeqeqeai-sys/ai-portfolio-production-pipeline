"""Phase B1 deterministic explainable heatmap and relative fragility intelligence."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Tuple

COMPONENT_FIELDS: Tuple[str, ...] = (
    "valuation_stretch_score",
    "fundamental_support_score",
    "narrative_saturation_score",
    "certainty_fragility_score",
    "structural_weakness_score",
)

ALL_SCORE_FIELDS: Tuple[str, ...] = ("ai_expectation_failure_score",) + COMPONENT_FIELDS

RISK_BANDS: Tuple[Tuple[str, int, int], ...] = (
    ("low", 0, 19),
    ("mild", 20, 39),
    ("elevated", 40, 59),
    ("high", 60, 79),
    ("severe", 80, 100),
)

DRIVER_TIE_ORDER: Tuple[str, ...] = (
    "structural_weakness_score",
    "certainty_fragility_score",
    "narrative_saturation_score",
    "valuation_stretch_score",
    "fundamental_support_score",
)

CLUSTER_ORDER: Tuple[str, ...] = (
    "broad_expectation_failure_cluster",
    "valuation_narrative_crowding_cluster",
    "structural_confirmation_cluster",
    "fundamental_support_gap_cluster",
    "certainty_fragility_cluster",
    "watchlist_cluster",
    "low_fragility_cluster",
)


def _round_half_up(value: float) -> int:
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _as_float(value):
    if isinstance(value, bool) or value is None:
        return None
    return float(value) if isinstance(value, (int, float)) else None


def _bound_score(value, field: str, missing_inputs: List[str], entity_flags: List[str]) -> int:
    numeric_value = _as_float(value)
    if numeric_value is None:
        missing_inputs.append(field)
        entity_flags.append(f"missing_input_fallback:{field}")
        return 50
    if numeric_value < 0:
        entity_flags.append(f"clamped_low:{field}")
        return 0
    if numeric_value > 100:
        entity_flags.append(f"clamped_high:{field}")
        return 100
    return _round_half_up(numeric_value)


def _score_band(score: int) -> str:
    for name, low, high in RISK_BANDS:
        if low <= score <= high:
            return name
    return "severe"


def _compute_drivers(component_scores: Dict[str, int]) -> Tuple[str, str]:
    ordered = sorted(DRIVER_TIE_ORDER, key=lambda key: (-component_scores[key], DRIVER_TIE_ORDER.index(key)))
    return ordered[0], ordered[1]


def _fragility_label(rank: int, total: int) -> str:
    top10_cut = max(1, (total + 9) // 10)
    top25_cut = max(top10_cut, (total + 3) // 4)
    bottom25_start = total - ((total + 3) // 4) + 1
    if rank <= top10_cut:
        return "highest_relative_fragility"
    if rank <= top25_cut:
        return "high_relative_fragility"
    if rank >= bottom25_start:
        return "lower_relative_fragility"
    return "moderate_relative_fragility"


def _cluster_label(score: int, components: Dict[str, int]) -> str:
    at_least_four_65 = sum(v >= 65 for v in components.values()) >= 4
    if score >= 75 and at_least_four_65:
        return "broad_expectation_failure_cluster"
    if components["valuation_stretch_score"] >= 70 and components["narrative_saturation_score"] >= 70:
        return "valuation_narrative_crowding_cluster"
    if components["structural_weakness_score"] >= 70 and score >= 65:
        return "structural_confirmation_cluster"
    if components["valuation_stretch_score"] >= 70 and components["fundamental_support_score"] >= 65:
        return "fundamental_support_gap_cluster"
    if components["certainty_fragility_score"] >= 70 and score >= 65:
        return "certainty_fragility_cluster"
    if score >= 50:
        return "watchlist_cluster"
    return "low_fragility_cluster"


def build_relative_fragility_ranking(entities: List[dict]) -> List[dict]:
    ranked = sorted(
        entities,
        key=lambda row: (
            -row["ai_expectation_failure_score"],
            -row["component_scores"]["structural_weakness_score"],
            -row["component_scores"]["narrative_saturation_score"],
            -row["component_scores"]["valuation_stretch_score"],
            row["ticker"],
        ),
    )
    total = len(ranked)
    output = []
    for index, row in enumerate(ranked, start=1):
        row_copy = dict(row)
        row_copy["rank"] = index
        row_copy["relative_fragility_label"] = _fragility_label(index, total)
        output.append(row_copy)
    return output


def build_fragility_cluster_summary(ranked_entities: List[dict]) -> Dict[str, object]:
    by_cluster = {name: [] for name in CLUSTER_ORDER}
    for entity in ranked_entities:
        by_cluster[entity["cluster_label"]].append(entity["ticker"])
    counts = {cluster: len(by_cluster[cluster]) for cluster in CLUSTER_ORDER}
    return {
        "cluster_order": list(CLUSTER_ORDER),
        "cluster_counts": counts,
        "cluster_members": {cluster: sorted(members) for cluster, members in by_cluster.items()},
        "dominant_cluster": sorted(CLUSTER_ORDER, key=lambda name: (-counts[name], CLUSTER_ORDER.index(name)))[0],
    }


def build_heatmap_evidence_summary(ranked_entities: List[dict]) -> Dict[str, object]:
    return {
        "required_input_fields": [
            "universe_name",
            "as_of_date",
            "entities",
            "ticker",
            "sector",
            "subsector",
            *ALL_SCORE_FIELDS,
            "data_quality_flags",
            "raw_evidence_refs",
        ],
        "output_evidence_fields": [
            "ranked_entities",
            "subsector_summaries",
            "cluster_summary",
            "missing_inputs",
            "data_quality_flags",
            "replay_metadata",
            "invariant_flags",
        ],
        "entity_count": len(ranked_entities),
    }


def _subsector_summaries(ranked_entities: List[dict]) -> List[dict]:
    groups: Dict[str, List[dict]] = {}
    for entity in ranked_entities:
        groups.setdefault(entity["subsector"], []).append(entity)
    summaries = []
    for subsector in sorted(groups.keys()):
        members = groups[subsector]
        avg = _round_half_up(sum(m["ai_expectation_failure_score"] for m in members) / len(members))
        max_score = max(m["ai_expectation_failure_score"] for m in members)
        severe = sum(m["score_band"] == "severe" for m in members)
        high_or_severe = sum(m["score_band"] in {"high", "severe"} for m in members)
        cluster_counts = {name: 0 for name in CLUSTER_ORDER}
        for m in members:
            cluster_counts[m["cluster_label"]] += 1
        dominant_cluster = sorted(CLUSTER_ORDER, key=lambda name: (-cluster_counts[name], CLUSTER_ORDER.index(name)))[0]
        top_entity = sorted(members, key=lambda m: (m["rank"], m["ticker"]))[0]["ticker"]
        summaries.append(
            {
                "subsector": subsector,
                "entity_count": len(members),
                "average_ai_expectation_failure_score": avg,
                "max_ai_expectation_failure_score": max_score,
                "severe_count": severe,
                "high_or_severe_count": high_or_severe,
                "dominant_cluster": dominant_cluster,
                "top_entity_by_fragility": top_entity,
                "explanation": f"Subsector {subsector} shows {dominant_cluster} with average fragility {avg}.",
            }
        )
    return summaries


def build_expectation_failure_heatmap(input_payload: dict) -> dict:
    payload = deepcopy(input_payload)
    processed = []
    all_missing: List[str] = []
    all_flags: List[str] = []
    for entity in payload.get("entities", []):
        item = deepcopy(entity)
        entity_flags = list(item.get("data_quality_flags") or [])
        missing_inputs: List[str] = []
        bounded_scores = {field: _bound_score(item.get(field), field, missing_inputs, entity_flags) for field in ALL_SCORE_FIELDS}
        components = {field: bounded_scores[field] for field in COMPONENT_FIELDS}
        dominant, secondary = _compute_drivers(components)
        cluster = _cluster_label(bounded_scores["ai_expectation_failure_score"], components)
        processed.append(
            {
                "ticker": item.get("ticker", "UNKNOWN"),
                "sector": item.get("sector", "UNKNOWN"),
                "subsector": item.get("subsector", "UNKNOWN"),
                "ai_expectation_failure_score": bounded_scores["ai_expectation_failure_score"],
                "score_band": _score_band(bounded_scores["ai_expectation_failure_score"]),
                "component_scores": components,
                "dominant_risk_driver": dominant,
                "secondary_risk_driver": secondary,
                "cluster_label": cluster,
                "explanation_template_id": "template_phase_b1_relative_fragility_v1",
                "explanation": f"Relative fragility is driven by {dominant} then {secondary}; assigned to {cluster}.",
                "data_quality_flags": sorted(set(entity_flags)),
                "raw_evidence_refs": list(item.get("raw_evidence_refs") or []),
            }
        )
        all_missing.extend([f"{item.get('ticker', 'UNKNOWN')}:{field}" for field in missing_inputs])
        all_flags.extend([f"{item.get('ticker', 'UNKNOWN')}:{flag}" for flag in sorted(set(entity_flags))])

    ranked = build_relative_fragility_ranking(processed)
    for row in ranked:
        row.pop("cluster_label")
    ranked_with_cluster = []
    for row in ranked:
        source = next(p for p in processed if p["ticker"] == row["ticker"])
        with_cluster = dict(row)
        with_cluster["cluster_label"] = source["cluster_label"]
        ranked_with_cluster.append(with_cluster)

    return {
        "module": "Phase B1 Explainable Heatmap & Relative Fragility Intelligence",
        "universe_name": payload.get("universe_name", "UNKNOWN"),
        "as_of_date": payload.get("as_of_date", "UNKNOWN"),
        "entity_count": len(ranked_with_cluster),
        "ranked_entities": ranked_with_cluster,
        "subsector_summaries": _subsector_summaries(ranked_with_cluster),
        "cluster_summary": build_fragility_cluster_summary(ranked_with_cluster),
        "heatmap_evidence_summary": build_heatmap_evidence_summary(ranked_with_cluster),
        "missing_inputs": sorted(set(all_missing)),
        "data_quality_flags": sorted(set(all_flags)),
        "replay_metadata": {
            "module": "phase_b1_expectation_failure_heatmap",
            "version": "v1",
            "deterministic_replay_key_fields": ["universe_name", "as_of_date", "entities"],
        },
        "invariant_flags": {
            "deterministic_output": True,
            "replay_compatible": True,
            "immutable_input_safe": True,
            "bounded_score": True,
            "fixed_thresholds_used": True,
            "fixed_ranking_rules_used": True,
            "fixed_cluster_rules_used": True,
            "fixed_template_explanation": True,
            "additive_only_architecture": True,
            "no_runtime_mutation": True,
            "no_phase_a_recomputation": True,
            "no_autonomous_trading": True,
            "no_prediction_engine": True,
            "no_optimization_loop": True,
            "no_adaptive_control": True,
            "no_portfolio_construction": True,
        },
    }


def build_phase_b1_heatmap_report() -> dict:
    return {
        "phase": "Phase B1",
        "module": "Explainable Heatmap & Relative Fragility Intelligence",
        "status": "complete_deterministic_intelligence_payload",
        "public_api": [
            "build_expectation_failure_heatmap",
            "build_relative_fragility_ranking",
            "build_fragility_cluster_summary",
            "build_heatmap_evidence_summary",
            "build_phase_b1_heatmap_report",
        ],
        "scoring_scope": {"bounded_range": [0, 100], "fallback_missing_or_invalid": 50, "no_phase_a_recompute": True},
        "ranking_rules": "ai_expectation_failure desc, structural_weakness desc, narrative_saturation desc, valuation_stretch desc, ticker asc",
        "cluster_rules": list(CLUSTER_ORDER),
        "subsector_summary_fields": [
            "subsector",
            "entity_count",
            "average_ai_expectation_failure_score",
            "max_ai_expectation_failure_score",
            "severe_count",
            "high_or_severe_count",
            "dominant_cluster",
            "top_entity_by_fragility",
            "explanation",
        ],
        "evidence_fields": ["data_quality_flags", "raw_evidence_refs", "missing_inputs", "replay_metadata"],
        "invariant_flags": build_expectation_failure_heatmap({"entities": []})["invariant_flags"],
        "implementation_boundaries": {
            "trading_signals": "excluded",
            "prediction": "excluded",
            "optimization": "excluded",
            "portfolio_construction": "excluded",
            "dashboard_ui": "excluded",
        },
        "supervisor_decision": "APPROVED_FOR_PHASE_B1_PR",
    }
