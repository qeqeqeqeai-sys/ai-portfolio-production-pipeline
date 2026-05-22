"""Phase A5 deterministic Certainty Fragility scoring module."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Tuple

from .phase_a1_contracts import SCORE_BANDS, build_expectation_failure_invariant_flags


REQUIRED_INPUT_FIELDS: Tuple[str, ...] = (
    "ticker",
    "sector",
    "subsector",
    "estimate_dispersion",
    "revenue_revision_instability",
    "eps_revision_instability",
    "execution_dependency",
    "customer_concentration",
    "product_concentration",
    "margin_expansion_dependency",
    "competitive_intensity",
    "uncertainty_concentration",
    "data_quality_flags",
    "raw_evidence_refs",
)


def build_certainty_fragility_thresholds() -> Dict[str, object]:
    return {
        "normalized_0_100_risk_bands": (
            {"id": "lt_20", "score": 15},
            {"id": "20_to_39", "score": 35},
            {"id": "40_to_59", "score": 55},
            {"id": "60_to_79", "score": 75},
            {"id": "gte_80", "score": 95},
        ),
        "fallback_missing_or_invalid_score": 50,
        "weights": {
            "estimate_dispersion_risk_score": 0.20,
            "revision_instability_risk_score": 0.20,
            "execution_dependency_risk_score": 0.25,
            "concentration_risk_score": 0.15,
            "competitive_uncertainty_risk_score": 0.20,
        },
    }


def build_certainty_fragility_subcomponent_contract() -> Dict[str, object]:
    return {
        "score_name": "certainty_fragility_score",
        "subcomponents": (
            "estimate_dispersion_risk_score",
            "revision_instability_risk_score",
            "execution_dependency_risk_score",
            "concentration_risk_score",
            "competitive_uncertainty_risk_score",
        ),
        "score_range": (0, 100),
        "fixed_weighting": build_certainty_fragility_thresholds()["weights"],
        "band_contract": SCORE_BANDS,
    }


def build_certainty_fragility_evidence_summary() -> Dict[str, Tuple[str, ...]]:
    return {
        "required_input_fields": REQUIRED_INPUT_FIELDS,
        "output_evidence_fields": (
            "subcomponent_scores",
            "thresholds_triggered",
            "missing_inputs",
            "data_quality_flags",
            "raw_evidence_refs",
        ),
    }


def _as_float(v):
    if isinstance(v, bool) or v is None:
        return None
    return float(v) if isinstance(v, (int, float)) else None


def _banded_risk(v: float) -> Tuple[int, str]:
    if v < 20:
        return 15, "lt_20"
    if v < 40:
        return 35, "20_to_39"
    if v < 60:
        return 55, "40_to_59"
    if v < 80:
        return 75, "60_to_79"
    return 95, "gte_80"


def _avg(scores: List[int]) -> int:
    return int(Decimal(str(sum(scores) / len(scores))).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _score_band(score_value: int) -> str:
    for band, (low, high) in SCORE_BANDS.items():
        if low <= score_value <= high:
            return band
    return "severe"


def _score_pair_component(payload: dict, fields: Tuple[str, str], label: str, missing_inputs: List[str], triggers: List[str]) -> int:
    scores: List[int] = []
    for field in fields:
        value = _as_float(payload.get(field))
        if value is None:
            continue
        score, trigger_id = _banded_risk(value)
        scores.append(score)
        triggers.append(f"{label}:{field}:{trigger_id}")
    if not scores:
        missing_inputs.append(label)
        triggers.append(f"{label}:missing_or_invalid")
        return 50
    return _avg(scores)


def score_certainty_fragility(input_payload: dict) -> dict:
    if not isinstance(input_payload, dict):
        raise TypeError("input_payload must be a dict")

    payload = deepcopy(input_payload)
    missing_inputs: List[str] = []
    triggers: List[str] = []

    estimate_dispersion = _as_float(payload.get("estimate_dispersion"))
    if estimate_dispersion is None:
        estimate_dispersion_score = 50
        missing_inputs.append("estimate_dispersion")
        triggers.append("estimate_dispersion_risk_score:missing_or_invalid")
    else:
        estimate_dispersion_score, trigger_id = _banded_risk(estimate_dispersion)
        triggers.append(f"estimate_dispersion_risk_score:{trigger_id}")

    revision_instability_score = _score_pair_component(
        payload,
        ("revenue_revision_instability", "eps_revision_instability"),
        "revision_instability_risk_score",
        missing_inputs,
        triggers,
    )
    execution_dependency_score = _score_pair_component(
        payload,
        ("execution_dependency", "margin_expansion_dependency"),
        "execution_dependency_risk_score",
        missing_inputs,
        triggers,
    )
    concentration_score = _score_pair_component(
        payload,
        ("customer_concentration", "product_concentration"),
        "concentration_risk_score",
        missing_inputs,
        triggers,
    )
    competitive_uncertainty_score = _score_pair_component(
        payload,
        ("competitive_intensity", "uncertainty_concentration"),
        "competitive_uncertainty_risk_score",
        missing_inputs,
        triggers,
    )

    subcomponent_scores = {
        "estimate_dispersion_risk_score": estimate_dispersion_score,
        "revision_instability_risk_score": revision_instability_score,
        "execution_dependency_risk_score": execution_dependency_score,
        "concentration_risk_score": concentration_score,
        "competitive_uncertainty_risk_score": competitive_uncertainty_score,
    }

    weights = build_certainty_fragility_thresholds()["weights"]
    weighted_score = sum(subcomponent_scores[name] * weight for name, weight in weights.items())
    score_value = max(0, min(100, int(Decimal(str(weighted_score)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))))
    score_band = _score_band(score_value)

    limited_data = bool(missing_inputs)
    template_id = "template_certainty_fragility_limited_data_v1" if limited_data else "template_certainty_fragility_band_v1"
    explanation_template = (
        "Certainty Fragility is {score_band} because {trigger_count} certainty-fragility conditions were triggered, including {primary_trigger}."
        if not limited_data
        else "Certainty Fragility is {score_band} with limited data because {trigger_count} certainty-fragility conditions were triggered, including {primary_trigger}."
    )
    explanation = explanation_template.format(
        score_band=score_band,
        trigger_count=len(triggers),
        primary_trigger=triggers[0] if triggers else "none",
    )

    return {
        "score_name": "certainty_fragility_score",
        "ticker": payload.get("ticker", "UNKNOWN"),
        "sector": payload.get("sector", "UNKNOWN"),
        "subsector": payload.get("subsector", "UNKNOWN"),
        "score_value": score_value,
        "score_band": score_band,
        "subcomponent_scores": subcomponent_scores,
        "thresholds_triggered": triggers,
        "missing_inputs": sorted(set(missing_inputs)),
        "data_quality_flags": list(payload.get("data_quality_flags") or []),
        "raw_evidence_refs": list(payload.get("raw_evidence_refs") or []),
        "explanation_template_id": template_id,
        "explanation": explanation,
        "replay_metadata": {
            "module": "phase_a5_certainty_fragility",
            "version": "v1",
            "deterministic_replay_key_fields": list(build_certainty_fragility_evidence_summary()["required_input_fields"]),
        },
        "invariant_flags": build_expectation_failure_invariant_flags(),
    }


def build_phase_a5_certainty_fragility_report() -> Dict[str, object]:
    thresholds = build_certainty_fragility_thresholds()
    return {
        "phase": "Phase A5",
        "module": "Certainty Fragility Score Module",
        "status": "complete_deterministic_subcomponent_scoring",
        "public_api": [
            "score_certainty_fragility",
            "build_certainty_fragility_thresholds",
            "build_certainty_fragility_subcomponent_contract",
            "build_certainty_fragility_evidence_summary",
            "build_phase_a5_certainty_fragility_report",
        ],
        "scoring_scope": "certainty_fragility_score_only",
        "score_direction": "0_durable_well_supported_certainty_100_severe_certainty_fragility_high_expectation_failure_risk",
        "subcomponents": list(build_certainty_fragility_subcomponent_contract()["subcomponents"]),
        "thresholds": thresholds,
        "weights": thresholds["weights"],
        "evidence_fields": list(build_certainty_fragility_evidence_summary()["output_evidence_fields"]),
        "invariant_flags": build_expectation_failure_invariant_flags(),
        "implementation_boundaries": [
            "phase_a5_only_no_composite_ai_expectation_failure_score",
            "no_structural_weakness_heatmaps_pair_analysis_benchmark_comparison_or_composite_scoring",
            "no_prediction_trading_optimization_agents_or_adaptive_behavior",
            "deterministic_fixed_thresholds_and_templates_only",
        ],
        "supervisor_decision": "APPROVED_FOR_PHASE_A5_PR",
    }
