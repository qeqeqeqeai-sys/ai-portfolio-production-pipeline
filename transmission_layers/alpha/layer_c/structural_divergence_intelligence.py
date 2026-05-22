from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Dict, Mapping, Sequence, Tuple

DIVERGENCE_CLASSIFICATIONS: Tuple[str, ...] = (
    "aligned_strength",
    "early_divergence",
    "confirmed_divergence",
    "hidden_fragility",
    "structural_breakdown",
    "insufficient_data",
    "invalid_input",
)

REQUIRED_METRICS: Tuple[str, ...] = (
    "index_strength_score",
    "breadth_support_score",
    "leadership_concentration_score",
    "cross_asset_confirmation_score",
    "transmission_consistency_score",
)


def _invariants() -> Dict[str, bool]:
    return {
        "deterministic_output": True,
        "replay_compatible": True,
        "immutable_input_safe": True,
        "no_runtime_mutation": True,
        "no_adaptive_control": True,
        "no_black_box_ml": True,
        "no_trading_execution": True,
    }


def _fingerprint(payload: Mapping[str, Any]) -> str:
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _coerce_score(source: Mapping[str, Any], key: str) -> float | None:
    value = source.get(key)
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _round(x: float) -> float:
    return round(x, 8)


def _clamp_unit_interval(x: float) -> float:
    return min(1.0, max(0.0, x))


def _classify(index_strength: float, divergence: float, fragility: float) -> str:
    if index_strength < 0.30 and fragility >= 0.70:
        return "structural_breakdown"
    if index_strength >= 0.70 and fragility >= 0.75:
        return "hidden_fragility"
    if divergence >= 0.65:
        return "confirmed_divergence"
    if divergence >= 0.40:
        return "early_divergence"
    return "aligned_strength"


def run_alpha_layer_c_structural_divergence_intelligence(
    *,
    structural_inputs: Mapping[str, Any],
    alpha_layer_a_output: Mapping[str, Any] | None = None,
    alpha_layer_b_output: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    base: Dict[str, Any] = {"invariants": _invariants()}
    if not isinstance(structural_inputs, Mapping):
        payload = {**base, "classification": "invalid_input", "explanation": "Structural divergence invalid_input: structural_inputs must be a mapping.", "component_contribution_map": {}, "metrics": {}}
        payload["replay_metadata"] = {"schema_version": "alpha_layer_c_v1", "fingerprint_sha256": _fingerprint(payload)}
        return payload

    scores: Dict[str, float] = {}
    for metric in REQUIRED_METRICS:
        value = _coerce_score(structural_inputs, metric)
        if value is None:
            payload = {**base, "classification": "insufficient_data", "explanation": f"Structural divergence insufficient_data: missing metric {metric}.", "component_contribution_map": {}, "metrics": {}}
            payload["replay_metadata"] = {"schema_version": "alpha_layer_c_v1", "fingerprint_sha256": _fingerprint(payload)}
            return payload
        if value < 0.0 or value > 1.0:
            payload = {**base, "classification": "invalid_input", "explanation": f"Structural divergence invalid_input: {metric} must be within [0, 1].", "component_contribution_map": {}, "metrics": {}}
            payload["replay_metadata"] = {"schema_version": "alpha_layer_c_v1", "fingerprint_sha256": _fingerprint(payload)}
            return payload
        scores[metric] = value

    index_strength = scores["index_strength_score"]
    breadth_gap = 1.0 - scores["breadth_support_score"]
    concentration_pressure = scores["leadership_concentration_score"]
    cross_asset_gap = 1.0 - scores["cross_asset_confirmation_score"]
    transmission_gap = 1.0 - scores["transmission_consistency_score"]

    a_penalty = 0.0
    if isinstance(alpha_layer_a_output, Mapping) and str(alpha_layer_a_output.get("classification", "")) in {
        "weak_negative_efficacy",
        "moderate_negative_efficacy",
        "strong_negative_efficacy",
    }:
        a_penalty = 0.05

    b_penalty = 0.0
    if isinstance(alpha_layer_b_output, Mapping):
        outcomes = alpha_layer_b_output.get("regime_results", [])
        if isinstance(outcomes, Sequence) and outcomes:
            adverse = sum(1 for row in outcomes if str(row.get("regime_outcome", "")) in {"fails", "decays", "inverts"})
            b_penalty = min(0.10, (adverse / len(outcomes)) * 0.10)

    contribution_map = {
        "index_strength_contribution": _round(0.35 * index_strength),
        "breadth_deterioration_contribution": _round(0.20 * breadth_gap),
        "leadership_concentration_contribution": _round(0.20 * concentration_pressure),
        "cross_asset_disagreement_contribution": _round(0.15 * cross_asset_gap),
        "transmission_inconsistency_contribution": _round(0.10 * transmission_gap),
        "alpha_layer_a_penalty": _round(a_penalty),
        "alpha_layer_b_penalty": _round(b_penalty),
    }
    raw_divergence_score = sum(contribution_map.values())
    divergence_score = _round(_clamp_unit_interval(raw_divergence_score))
    fragility_score = _round(
        _clamp_unit_interval(
            (0.35 * concentration_pressure) + (0.25 * breadth_gap) + (0.20 * transmission_gap) + (0.20 * cross_asset_gap)
        )
    )
    classification = _classify(index_strength, divergence_score, fragility_score)

    contribution_map["raw_divergence_score"] = _round(raw_divergence_score)
    contribution_map["divergence_score_clamped"] = divergence_score
    contribution_map["reconciliation_residual"] = _round(divergence_score - _clamp_unit_interval(raw_divergence_score))

    metrics = {
        **{k: _round(v) for k, v in scores.items()},
        "divergence_score": divergence_score,
        "fragility_score": fragility_score,
    }

    payload = {
        **base,
        "classification": classification,
        "metrics": metrics,
        "component_contribution_map": contribution_map,
        "explanation": (
            "Structural divergence classification={classification}; index_strength={index:.4f}, breadth_support={breadth:.4f}, "
            "leadership_concentration={concentration:.4f}, cross_asset_confirmation={cross:.4f}, transmission_consistency={transmission:.4f}, "
            "divergence_score={divergence:.4f}, fragility_score={fragility:.4f}."
        ).format(
            classification=classification,
            index=index_strength,
            breadth=scores["breadth_support_score"],
            concentration=concentration_pressure,
            cross=scores["cross_asset_confirmation_score"],
            transmission=scores["transmission_consistency_score"],
            divergence=divergence_score,
            fragility=fragility_score,
        ),
        "invariant_flags": _invariants(),
    }
    payload["replay_metadata"] = {"schema_version": "alpha_layer_c_v1", "fingerprint_sha256": _fingerprint(payload)}
    return payload
