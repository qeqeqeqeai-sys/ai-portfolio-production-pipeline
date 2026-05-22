from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Dict, Mapping

NARRATIVE_FRAGILITY_CLASSIFICATIONS = (
    "structurally_supported_narrative",
    "overheated_but_supported",
    "early_narrative_fragility",
    "confirmed_narrative_fragility",
    "narrative_exhaustion_risk",
    "speculative_concentration_risk",
    "insufficient_data",
    "invalid_input",
)

REQUIRED_METRICS = (
    "narrative_strength_score",
    "hype_intensity_score",
    "sentiment_persistence_score",
    "valuation_pressure_score",
    "breadth_support_score",
    "transmission_quality_score",
    "fundamentals_support_score",
    "leadership_concentration_score",
    "liquidity_support_score",
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
        "bounded_outputs": True,
        "additive_only": True,
    }


def _round(x: float) -> float:
    return round(x, 8)


def _clamp(x: float) -> float:
    return min(1.0, max(0.0, x))


def _coerce_score(source: Mapping[str, Any], key: str) -> float | None:
    value = source.get(key)
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _fingerprint(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(canonical.encode("utf-8")).hexdigest()


def _terminal_payload(base: Mapping[str, Any], classification: str, explanation: str) -> Dict[str, Any]:
    payload = {
        **base,
        "narrative_fragility_classification": classification,
        "computed_metrics": {},
        "component_contribution_map": {},
        "deterministic_explanation": explanation,
        "classification_rule_applied": classification,
        "invariant_flags": _invariants(),
    }
    payload["replay_metadata"] = {"schema_version": "alpha_layer_d_v1", "fingerprint_sha256": _fingerprint(payload)}
    return payload


def _classify(*, narrative_strength: float, structural_support: float, overheating: float, fragility: float, concentration_fragility: float) -> tuple[str, str]:
    if narrative_strength >= 0.65 and structural_support >= 0.70 and fragility < 0.35 and overheating < 0.65:
        return "structurally_supported_narrative", "precedence_1_structurally_supported_narrative"
    if overheating >= 0.70 and structural_support >= 0.55 and fragility < 0.55:
        return "overheated_but_supported", "precedence_2_overheated_but_supported"
    if fragility >= 0.74 and structural_support < 0.35 and narrative_strength >= 0.65:
        return "narrative_exhaustion_risk", "precedence_3_narrative_exhaustion_risk"
    if concentration_fragility >= 0.78 and structural_support < 0.52:
        return "speculative_concentration_risk", "precedence_4_speculative_concentration_risk"
    if fragility >= 0.50:
        return "confirmed_narrative_fragility", "precedence_5_confirmed_narrative_fragility"
    return "early_narrative_fragility", "precedence_6_early_narrative_fragility"


def run_alpha_layer_d_narrative_fragility(
    *,
    narrative_inputs: Mapping[str, Any],
    alpha_layer_c_output: Mapping[str, Any] | None = None,
    alpha_layer_a_output: Mapping[str, Any] | None = None,
    alpha_layer_b_output: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    del alpha_layer_a_output
    del alpha_layer_b_output

    base: Dict[str, Any] = {"invariants": _invariants()}
    if not isinstance(narrative_inputs, Mapping):
        return _terminal_payload(base, "invalid_input", "Narrative fragility invalid_input: narrative_inputs must be a mapping.")

    scores: Dict[str, float] = {}
    for metric in REQUIRED_METRICS:
        value = _coerce_score(narrative_inputs, metric)
        if value is None:
            return _terminal_payload(base, "insufficient_data", f"Narrative fragility insufficient_data: missing metric {metric}.")
        if value < 0.0 or value > 1.0:
            return _terminal_payload(base, "invalid_input", f"Narrative fragility invalid_input: {metric} must be within [0, 1].")
        scores[metric] = value

    hype_valuation_gap = _round(_clamp(scores["hype_intensity_score"] - (0.70 * scores["valuation_pressure_score"])))
    structural_support_score = _round(_clamp((0.35 * scores["breadth_support_score"]) + (0.30 * scores["transmission_quality_score"]) + (0.25 * scores["fundamentals_support_score"]) + (0.10 * scores["liquidity_support_score"])))
    narrative_support_gap = _round(_clamp(scores["narrative_strength_score"] - structural_support_score))
    sentiment_structure_gap = _round(_clamp(scores["sentiment_persistence_score"] - ((scores["breadth_support_score"] + scores["transmission_quality_score"]) / 2.0)))

    c_penalty = 0.0
    if isinstance(alpha_layer_c_output, Mapping):
        if str(alpha_layer_c_output.get("classification", "")) in {"early_divergence", "confirmed_divergence", "hidden_fragility", "structural_breakdown"}:
            c_penalty = 0.08

    concentration_fragility_score = _round(_clamp((0.60 * scores["leadership_concentration_score"]) + (0.25 * (1.0 - scores["breadth_support_score"])) + (0.15 * (1.0 - scores["liquidity_support_score"]))))

    contribution_map = {
        "narrative_support_gap_contribution": _round(0.34 * narrative_support_gap),
        "sentiment_structure_gap_contribution": _round(0.24 * sentiment_structure_gap),
        "hype_valuation_gap_contribution": _round(0.22 * hype_valuation_gap),
        "concentration_fragility_contribution": _round(0.20 * concentration_fragility_score),
        "alpha_layer_c_fragility_penalty": _round(c_penalty),
    }
    raw_fragility = _round(sum(contribution_map.values()))
    narrative_fragility_score = _round(_clamp(raw_fragility))
    overheating_score = _round(_clamp((0.45 * scores["hype_intensity_score"]) + (0.35 * scores["valuation_pressure_score"]) + (0.20 * scores["sentiment_persistence_score"])))

    classification, classification_rule = _classify(
        narrative_strength=scores["narrative_strength_score"],
        structural_support=structural_support_score,
        overheating=overheating_score,
        fragility=narrative_fragility_score,
        concentration_fragility=concentration_fragility_score,
    )

    contribution_map["raw_fragility_score"] = raw_fragility
    contribution_map["narrative_fragility_score_clamped"] = narrative_fragility_score
    contribution_map["reconciliation_residual"] = _round(narrative_fragility_score - _clamp(raw_fragility))

    computed_metrics = {
        "hype_valuation_gap": hype_valuation_gap,
        "narrative_support_gap": narrative_support_gap,
        "sentiment_structure_gap": sentiment_structure_gap,
        "concentration_fragility_score": concentration_fragility_score,
        "narrative_fragility_score": narrative_fragility_score,
        "structural_support_score": structural_support_score,
        "overheating_score": overheating_score,
    }

    explanation = (
        "Narrative fragility analysis: narrative strength={narrative_strength:.4f}; "
        "hype intensity={hype:.4f} and valuation pressure={valuation:.4f}; "
        "support quality={support:.4f}; breadth/transmission condition breadth={breadth:.4f}, transmission={transmission:.4f}; "
        "concentration risk={concentration:.4f}; final bounded classification={classification}."
    ).format(
        narrative_strength=scores["narrative_strength_score"],
        hype=scores["hype_intensity_score"],
        valuation=scores["valuation_pressure_score"],
        support=structural_support_score,
        breadth=scores["breadth_support_score"],
        transmission=scores["transmission_quality_score"],
        concentration=concentration_fragility_score,
        classification=classification,
    )

    payload = {
        **base,
        "narrative_fragility_classification": classification,
        "computed_metrics": computed_metrics,
        "component_contribution_map": contribution_map,
        "deterministic_explanation": explanation,
        "classification_rule_applied": classification_rule,
        "invariant_flags": _invariants(),
    }
    payload["replay_metadata"] = {"schema_version": "alpha_layer_d_v1", "fingerprint_sha256": _fingerprint(payload)}
    return payload
