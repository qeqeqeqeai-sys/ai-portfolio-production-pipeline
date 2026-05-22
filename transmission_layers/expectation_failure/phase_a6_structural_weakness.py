"""Phase A6 deterministic Structural Weakness bridge scoring module."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Tuple

from .phase_a1_contracts import SCORE_BANDS, build_expectation_failure_invariant_flags


REQUIRED_INPUT_FIELDS: Tuple[str, ...] = (
    "ticker",
    "sector",
    "subsector",
    "fragility_score",
    "transmission_instability_score",
    "divergence_score",
    "regime_stress_score",
    "structural_deterioration_score",
    "propagation_weakness_score",
    "data_quality_flags",
    "raw_evidence_refs",
)


def build_structural_weakness_thresholds() -> Dict[str, object]:
    return {
        "fallback_missing_or_invalid_score": 50,
        "component_triggers": {
            "elevated_trigger_min": 40,
            "high_trigger_min": 60,
            "severe_trigger_min": 80,
        },
        "weights": {
            "fragility_risk_score": 0.25,
            "transmission_instability_risk_score": 0.20,
            "divergence_risk_score": 0.20,
            "regime_stress_risk_score": 0.15,
            "deterioration_propagation_risk_score": 0.20,
        },
    }


def build_structural_weakness_subcomponent_contract() -> Dict[str, object]:
    return {
        "score_name": "structural_weakness_score",
        "subcomponents": (
            "fragility_risk_score",
            "transmission_instability_risk_score",
            "divergence_risk_score",
            "regime_stress_risk_score",
            "deterioration_propagation_risk_score",
        ),
        "score_range": (0, 100),
        "fixed_weighting": build_structural_weakness_thresholds()["weights"],
        "band_contract": SCORE_BANDS,
    }


def build_structural_weakness_evidence_summary() -> Dict[str, Tuple[str, ...]]:
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


def _round_half_up(value: float) -> int:
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _score_band(score_value: int) -> str:
    for band, (low, high) in SCORE_BANDS.items():
        if low <= score_value <= high:
            return band
    return "severe"


def _bound_or_fallback(payload: dict, field: str, missing: List[str], flags: List[str]) -> int:
    value = _as_float(payload.get(field))
    if value is None:
        missing.append(field)
        return 50
    if value < 0:
        flags.append(f"clamped_low:{field}")
        return 0
    if value > 100:
        flags.append(f"clamped_high:{field}")
        return 100
    return _round_half_up(value)


def _triggers_for_subcomponent(name: str, score: int) -> List[str]:
    thresholds = build_structural_weakness_thresholds()["component_triggers"]
    out: List[str] = []
    if score >= thresholds["elevated_trigger_min"]:
        out.append(f"{name}:elevated_trigger")
    if score >= thresholds["high_trigger_min"]:
        out.append(f"{name}:high_trigger")
    if score >= thresholds["severe_trigger_min"]:
        out.append(f"{name}:severe_trigger")
    return out


def _build_invariant_flags() -> Dict[str, bool]:
    flags = dict(build_expectation_failure_invariant_flags())
    flags["no_upstream_mutation"] = True
    flags["bridge_only_mapping"] = True
    return flags


def score_structural_weakness(input_payload: dict) -> dict:
    if not isinstance(input_payload, dict):
        raise TypeError("input_payload must be a dict")

    payload = deepcopy(input_payload)
    missing_inputs: List[str] = []
    added_quality_flags: List[str] = []

    fragility = _bound_or_fallback(payload, "fragility_score", missing_inputs, added_quality_flags)
    transmission_instability = _bound_or_fallback(payload, "transmission_instability_score", missing_inputs, added_quality_flags)
    divergence = _bound_or_fallback(payload, "divergence_score", missing_inputs, added_quality_flags)
    regime_stress = _bound_or_fallback(payload, "regime_stress_score", missing_inputs, added_quality_flags)

    det = _as_float(payload.get("structural_deterioration_score"))
    prop = _as_float(payload.get("propagation_weakness_score"))
    det_score = _bound_or_fallback(payload, "structural_deterioration_score", [], added_quality_flags) if det is not None else None
    prop_score = _bound_or_fallback(payload, "propagation_weakness_score", [], added_quality_flags) if prop is not None else None
    if det_score is None and prop_score is None:
        deterioration_propagation = 50
        missing_inputs.append("deterioration_propagation_risk_score")
    elif det_score is None:
        deterioration_propagation = prop_score
    elif prop_score is None:
        deterioration_propagation = det_score
    else:
        deterioration_propagation = _round_half_up((det_score + prop_score) / 2)

    subcomponent_scores = {
        "fragility_risk_score": fragility,
        "transmission_instability_risk_score": transmission_instability,
        "divergence_risk_score": divergence,
        "regime_stress_risk_score": regime_stress,
        "deterioration_propagation_risk_score": deterioration_propagation,
    }

    thresholds_triggered: List[str] = []
    for name, score in subcomponent_scores.items():
        thresholds_triggered.extend(_triggers_for_subcomponent(name, score))

    weights = build_structural_weakness_thresholds()["weights"]
    weighted_score = sum(subcomponent_scores[name] * weight for name, weight in weights.items())
    score_value = max(0, min(100, _round_half_up(weighted_score)))
    score_band = _score_band(score_value)

    limited_data = bool(missing_inputs)
    template_id = "template_structural_weakness_limited_data_v1" if limited_data else "template_structural_weakness_band_v1"
    explanation_template = (
        "Structural Weakness is {score_band} because {trigger_count} structural weakness conditions were triggered, including {primary_trigger}."
        if not limited_data
        else "Structural Weakness is {score_band} with limited data because {trigger_count} structural weakness conditions were triggered, including {primary_trigger}."
    )
    explanation = explanation_template.format(
        score_band=score_band,
        trigger_count=len(thresholds_triggered),
        primary_trigger=thresholds_triggered[0] if thresholds_triggered else "none",
    )

    data_quality_flags = list(payload.get("data_quality_flags") or []) + added_quality_flags

    return {
        "score_name": "structural_weakness_score",
        "ticker": payload.get("ticker", "UNKNOWN"),
        "sector": payload.get("sector", "UNKNOWN"),
        "subsector": payload.get("subsector", "UNKNOWN"),
        "score_value": score_value,
        "score_band": score_band,
        "subcomponent_scores": subcomponent_scores,
        "thresholds_triggered": thresholds_triggered,
        "missing_inputs": sorted(set(missing_inputs)),
        "data_quality_flags": data_quality_flags,
        "raw_evidence_refs": list(payload.get("raw_evidence_refs") or []),
        "explanation_template_id": template_id,
        "explanation": explanation,
        "replay_metadata": {
            "module": "phase_a6_structural_weakness",
            "version": "v1",
            "deterministic_replay_key_fields": list(build_structural_weakness_evidence_summary()["required_input_fields"]),
        },
        "invariant_flags": _build_invariant_flags(),
    }


def build_phase_a6_structural_weakness_report() -> Dict[str, object]:
    thresholds = build_structural_weakness_thresholds()
    return {
        "phase": "Phase A6",
        "module": "Structural Weakness Bridge Module",
        "status": "complete_deterministic_bridge_scoring",
        "public_api": [
            "score_structural_weakness",
            "build_structural_weakness_thresholds",
            "build_structural_weakness_subcomponent_contract",
            "build_structural_weakness_evidence_summary",
            "build_phase_a6_structural_weakness_report",
        ],
        "scoring_scope": "structural_weakness_score_only",
        "score_direction": "0_structurally_resilient_low_weakness_100_severe_structural_weakness_high_expectation_failure_risk",
        "upstream_dependency_scope": [
            "fragility_score",
            "transmission_instability_score",
            "divergence_score",
            "regime_stress_score",
            "structural_deterioration_score",
            "propagation_weakness_score",
        ],
        "subcomponents": list(build_structural_weakness_subcomponent_contract()["subcomponents"]),
        "thresholds": thresholds,
        "weights": thresholds["weights"],
        "evidence_fields": list(build_structural_weakness_evidence_summary()["output_evidence_fields"]),
        "invariant_flags": _build_invariant_flags(),
        "implementation_boundaries": [
            "phase_a6_only_no_composite_ai_expectation_failure_score",
            "no_heatmaps_pair_analysis_benchmark_comparison_or_composite_scoring",
            "no_prediction_trading_optimization_agents_or_adaptive_behavior",
            "deterministic_fixed_thresholds_and_templates_only",
            "bridge_only_mapping_no_upstream_reinterpretation",
        ],
        "supervisor_decision": "APPROVED_FOR_PHASE_A6_PR",
    }
