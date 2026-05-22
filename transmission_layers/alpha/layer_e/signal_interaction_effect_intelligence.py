from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Dict, Mapping

INTERACTION_EFFECT_CLASSIFICATIONS = (
    "benign_interaction",
    "constructive_confirmation",
    "early_compound_fragility",
    "confirmed_compound_fragility",
    "severe_interaction_breakdown",
    "contradictory_signal_state",
    "insufficient_data",
    "invalid_input",
)

REQUIRED_METRICS = (
    "momentum_score",
    "breadth_support_score",
    "valuation_pressure_score",
    "hype_intensity_score",
    "sentiment_persistence_score",
    "transmission_quality_score",
    "structural_divergence_score",
    "narrative_fragility_score",
    "leadership_concentration_score",
    "liquidity_support_score",
    "credit_stress_score",
    "regime_stress_score",
    "factor_decay_score",
    "cross_asset_disagreement_score",
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
        "interaction_effect_classification": classification,
        "computed_metrics": {},
        "component_contribution_map": {},
        "classification_rule_applied": classification,
        "deterministic_explanation": explanation,
        "invariant_flags": _invariants(),
    }
    payload["replay_metadata"] = {"schema_version": "alpha_layer_e_v1", "fingerprint_sha256": _fingerprint(payload)}
    return payload


def run_alpha_layer_e_signal_interaction_effects(
    *,
    signal_inputs: Mapping[str, Any],
    alpha_layer_a_output: Mapping[str, Any] | None = None,
    alpha_layer_b_output: Mapping[str, Any] | None = None,
    alpha_layer_c_output: Mapping[str, Any] | None = None,
    alpha_layer_d_output: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    base: Dict[str, Any] = {"invariants": _invariants()}
    if not isinstance(signal_inputs, Mapping):
        return _terminal_payload(base, "invalid_input", "Signal interaction invalid_input: signal_inputs must be a mapping.")

    scores: Dict[str, float] = {}
    for metric in REQUIRED_METRICS:
        value = _coerce_score(signal_inputs, metric)
        if value is None:
            return _terminal_payload(base, "insufficient_data", f"Signal interaction insufficient_data: missing metric {metric}.")
        if value < 0.0 or value > 1.0:
            return _terminal_payload(base, "invalid_input", f"Signal interaction invalid_input: {metric} must be within [0, 1].")
        scores[metric] = _clamp(value)

    upstream_fragility_bonus = 0.0
    if isinstance(alpha_layer_c_output, Mapping) and str(alpha_layer_c_output.get("classification", "")) in {"confirmed_divergence", "hidden_fragility", "structural_breakdown"}:
        upstream_fragility_bonus += 0.03
    if isinstance(alpha_layer_d_output, Mapping) and str(alpha_layer_d_output.get("narrative_fragility_classification", "")) in {"confirmed_narrative_fragility", "narrative_exhaustion_risk", "speculative_concentration_risk"}:
        upstream_fragility_bonus += 0.03
    if isinstance(alpha_layer_a_output, Mapping) and str(alpha_layer_a_output.get("classification", "")).startswith("negative"):
        upstream_fragility_bonus += 0.02
    if isinstance(alpha_layer_b_output, Mapping) and str(alpha_layer_b_output.get("summary_status", "")) in {"deteriorating", "fragile"}:
        upstream_fragility_bonus += 0.02

    momentum_breadth_gap = _round(_clamp(scores["momentum_score"] - scores["breadth_support_score"]))
    valuation_hype_pressure = _round(_clamp((0.55 * scores["valuation_pressure_score"]) + (0.45 * scores["hype_intensity_score"])))
    sentiment_transmission_gap = _round(_clamp(scores["sentiment_persistence_score"] - scores["transmission_quality_score"]))
    divergence_narrative_overlap = _round(_clamp((0.50 * scores["structural_divergence_score"]) + (0.50 * scores["narrative_fragility_score"])))
    credit_liquidity_stress = _round(_clamp((0.60 * scores["credit_stress_score"]) + (0.40 * (1.0 - scores["liquidity_support_score"]))))
    concentration_participation_risk = _round(_clamp((0.60 * scores["leadership_concentration_score"]) + (0.40 * (1.0 - scores["breadth_support_score"]))))
    regime_decay_pressure = _round(_clamp((0.50 * scores["regime_stress_score"]) + (0.50 * scores["factor_decay_score"])))
    cross_asset_narrative_conflict = _round(_clamp((0.55 * scores["cross_asset_disagreement_score"]) + (0.45 * scores["sentiment_persistence_score"])))

    contribution_map = {
        "momentum_breadth_gap_contribution": _round(0.17 * momentum_breadth_gap),
        "valuation_hype_pressure_contribution": _round(0.11 * valuation_hype_pressure),
        "sentiment_transmission_gap_contribution": _round(0.13 * sentiment_transmission_gap),
        "divergence_narrative_overlap_contribution": _round(0.17 * divergence_narrative_overlap),
        "credit_liquidity_stress_contribution": _round(0.15 * credit_liquidity_stress),
        "concentration_participation_risk_contribution": _round(0.10 * concentration_participation_risk),
        "regime_decay_pressure_contribution": _round(0.10 * regime_decay_pressure),
        "cross_asset_narrative_conflict_contribution": _round(0.07 * cross_asset_narrative_conflict),
        "upstream_fragility_modifier": _round(upstream_fragility_bonus),
    }
    raw_interaction_fragility_score = _round(sum(contribution_map.values()))
    interaction_fragility_score = _round(_clamp(raw_interaction_fragility_score))
    confirmation_score = _round(
        _clamp(
            (0.40 * scores["momentum_score"])
            + (0.30 * scores["breadth_support_score"])
            + (0.15 * scores["liquidity_support_score"])
            + (0.15 * (1.0 - scores["cross_asset_disagreement_score"]))
        )
    )

    severe_breakdown = divergence_narrative_overlap >= 0.85 and sentiment_transmission_gap >= 0.55
    confirmed_fragility = momentum_breadth_gap >= 0.40 and concentration_participation_risk >= 0.65 and interaction_fragility_score >= 0.52
    contradictory_state = credit_liquidity_stress >= 0.68 and scores["momentum_score"] >= 0.70

    if severe_breakdown:
        classification = "severe_interaction_breakdown"
        rule = "precedence_3_severe_interaction_breakdown"
    elif confirmed_fragility:
        classification = "confirmed_compound_fragility"
        rule = "precedence_4_confirmed_compound_fragility"
    elif contradictory_state:
        classification = "contradictory_signal_state"
        rule = "precedence_5_contradictory_signal_state"
    elif interaction_fragility_score >= 0.34:
        classification = "early_compound_fragility"
        rule = "precedence_6_early_compound_fragility"
    elif confirmation_score >= 0.68 and interaction_fragility_score <= 0.28:
        classification = "constructive_confirmation"
        rule = "precedence_7_constructive_confirmation"
    else:
        classification = "benign_interaction"
        rule = "precedence_8_benign_interaction"

    contribution_map["raw_interaction_fragility_score"] = raw_interaction_fragility_score
    contribution_map["interaction_fragility_score_clamped"] = interaction_fragility_score
    contribution_map["reconciliation_residual"] = _round(interaction_fragility_score - _clamp(raw_interaction_fragility_score))

    computed_metrics = {
        "momentum_breadth_gap": momentum_breadth_gap,
        "valuation_hype_pressure": valuation_hype_pressure,
        "sentiment_transmission_gap": sentiment_transmission_gap,
        "divergence_narrative_overlap": divergence_narrative_overlap,
        "credit_liquidity_stress": credit_liquidity_stress,
        "concentration_participation_risk": concentration_participation_risk,
        "regime_decay_pressure": regime_decay_pressure,
        "cross_asset_narrative_conflict": cross_asset_narrative_conflict,
        "interaction_fragility_score": interaction_fragility_score,
        "confirmation_score": confirmation_score,
    }

    explanation = (
        "Signal interaction analysis: momentum/breadth condition momentum={momentum:.4f}, breadth={breadth:.4f}, gap={mb_gap:.4f}; "
        "valuation/hype pressure valuation={valuation:.4f}, hype={hype:.4f}, pressure={vh_pressure:.4f}; "
        "sentiment/transmission condition sentiment={sentiment:.4f}, transmission={transmission:.4f}, gap={st_gap:.4f}; "
        "divergence/narrative overlap divergence={divergence:.4f}, narrative_fragility={narrative:.4f}, overlap={dn_overlap:.4f}; "
        "credit/liquidity condition credit_stress={credit:.4f}, liquidity={liquidity:.4f}, stress={cl_stress:.4f}; "
        "concentration/participation risk concentration={concentration:.4f}, risk={cp_risk:.4f}; "
        "final bounded classification={classification}."
    ).format(
        momentum=scores["momentum_score"],
        breadth=scores["breadth_support_score"],
        mb_gap=momentum_breadth_gap,
        valuation=scores["valuation_pressure_score"],
        hype=scores["hype_intensity_score"],
        vh_pressure=valuation_hype_pressure,
        sentiment=scores["sentiment_persistence_score"],
        transmission=scores["transmission_quality_score"],
        st_gap=sentiment_transmission_gap,
        divergence=scores["structural_divergence_score"],
        narrative=scores["narrative_fragility_score"],
        dn_overlap=divergence_narrative_overlap,
        credit=scores["credit_stress_score"],
        liquidity=scores["liquidity_support_score"],
        cl_stress=credit_liquidity_stress,
        concentration=scores["leadership_concentration_score"],
        cp_risk=concentration_participation_risk,
        classification=classification,
    )

    payload = {
        **base,
        "interaction_effect_classification": classification,
        "computed_metrics": computed_metrics,
        "component_contribution_map": contribution_map,
        "classification_rule_applied": rule,
        "deterministic_explanation": explanation,
        "invariant_flags": _invariants(),
    }
    payload["replay_metadata"] = {"schema_version": "alpha_layer_e_v1", "fingerprint_sha256": _fingerprint(payload)}
    return payload
