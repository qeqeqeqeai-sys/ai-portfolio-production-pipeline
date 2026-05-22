from __future__ import annotations

from copy import deepcopy

from transmission_layers.alpha import INTERACTION_EFFECT_CLASSIFICATIONS, run_alpha_layer_e_signal_interaction_effects


def _base_inputs() -> dict[str, float]:
    return {
        "momentum_score": 0.45,
        "breadth_support_score": 0.60,
        "valuation_pressure_score": 0.42,
        "hype_intensity_score": 0.40,
        "sentiment_persistence_score": 0.46,
        "transmission_quality_score": 0.55,
        "structural_divergence_score": 0.32,
        "narrative_fragility_score": 0.30,
        "leadership_concentration_score": 0.38,
        "liquidity_support_score": 0.66,
        "credit_stress_score": 0.34,
        "regime_stress_score": 0.35,
        "factor_decay_score": 0.33,
        "cross_asset_disagreement_score": 0.30,
    }


def test_deterministic_repeated_output_and_fingerprint_stability() -> None:
    inputs = _base_inputs()
    one = run_alpha_layer_e_signal_interaction_effects(signal_inputs=inputs)
    two = run_alpha_layer_e_signal_interaction_effects(signal_inputs=inputs)
    assert one == two
    assert one["replay_metadata"]["fingerprint_sha256"] == two["replay_metadata"]["fingerprint_sha256"]


def test_benign_interaction() -> None:
    result = run_alpha_layer_e_signal_interaction_effects(signal_inputs=_base_inputs())
    assert result["interaction_effect_classification"] == "benign_interaction"


def test_constructive_confirmation() -> None:
    result = run_alpha_layer_e_signal_interaction_effects(
        signal_inputs={**_base_inputs(), "momentum_score": 0.82, "breadth_support_score": 0.80, "liquidity_support_score": 0.85, "cross_asset_disagreement_score": 0.10}
    )
    assert result["interaction_effect_classification"] == "constructive_confirmation"


def test_early_compound_fragility() -> None:
    result = run_alpha_layer_e_signal_interaction_effects(
        signal_inputs={**_base_inputs(), "momentum_score": 0.70, "breadth_support_score": 0.40, "valuation_pressure_score": 0.70, "hype_intensity_score": 0.75}
    )
    assert result["interaction_effect_classification"] == "early_compound_fragility"


def test_confirmed_compound_fragility() -> None:
    result = run_alpha_layer_e_signal_interaction_effects(
        signal_inputs={**_base_inputs(), "momentum_score": 0.88, "breadth_support_score": 0.30, "leadership_concentration_score": 0.90, "structural_divergence_score": 0.60, "narrative_fragility_score": 0.62, "valuation_pressure_score": 0.90, "hype_intensity_score": 0.92, "sentiment_persistence_score": 0.80, "transmission_quality_score": 0.30, "liquidity_support_score": 0.30, "credit_stress_score": 0.70, "regime_stress_score": 0.70, "factor_decay_score": 0.70, "cross_asset_disagreement_score": 0.60}
    )
    assert result["interaction_effect_classification"] == "confirmed_compound_fragility"


def test_severe_interaction_breakdown() -> None:
    result = run_alpha_layer_e_signal_interaction_effects(
        signal_inputs={**_base_inputs(), "structural_divergence_score": 0.95, "narrative_fragility_score": 0.92, "sentiment_persistence_score": 0.95, "transmission_quality_score": 0.20}
    )
    assert result["interaction_effect_classification"] == "severe_interaction_breakdown"


def test_contradictory_signal_state() -> None:
    result = run_alpha_layer_e_signal_interaction_effects(
        signal_inputs={**_base_inputs(), "credit_stress_score": 0.95, "liquidity_support_score": 0.15, "momentum_score": 0.78}
    )
    assert result["interaction_effect_classification"] == "contradictory_signal_state"


def test_invalid_input_and_insufficient_data() -> None:
    insufficient = run_alpha_layer_e_signal_interaction_effects(signal_inputs={"momentum_score": 0.5})
    assert insufficient["interaction_effect_classification"] == "insufficient_data"

    invalid = run_alpha_layer_e_signal_interaction_effects(signal_inputs={**_base_inputs(), "momentum_score": 2.0})
    assert invalid["interaction_effect_classification"] == "invalid_input"


def test_bounded_labels_scores_and_component_reconciliation() -> None:
    result = run_alpha_layer_e_signal_interaction_effects(signal_inputs=_base_inputs())
    assert result["interaction_effect_classification"] in INTERACTION_EFFECT_CLASSIFICATIONS

    for key in result["computed_metrics"]:
        assert 0.0 <= result["computed_metrics"][key] <= 1.0

    cmap = result["component_contribution_map"]
    contribution_sum = (
        cmap["momentum_breadth_gap_contribution"]
        + cmap["valuation_hype_pressure_contribution"]
        + cmap["sentiment_transmission_gap_contribution"]
        + cmap["divergence_narrative_overlap_contribution"]
        + cmap["credit_liquidity_stress_contribution"]
        + cmap["concentration_participation_risk_contribution"]
        + cmap["regime_decay_pressure_contribution"]
        + cmap["cross_asset_narrative_conflict_contribution"]
        + cmap["upstream_fragility_modifier"]
    )
    assert round(contribution_sum, 8) == cmap["raw_interaction_fragility_score"]
    assert cmap["interaction_fragility_score_clamped"] == result["computed_metrics"]["interaction_fragility_score"]
    assert cmap["reconciliation_residual"] == 0.0


def test_no_mutation_of_inputs_and_optional_upstream() -> None:
    inputs = _base_inputs()
    layer_a = {"classification": "negative_signal_quality", "meta": {"x": 1}}
    layer_b = {"summary_status": "fragile", "data": [1, 2]}
    layer_c = {"classification": "hidden_fragility", "metrics": {"z": 0.8}}
    layer_d = {"narrative_fragility_classification": "confirmed_narrative_fragility", "computed_metrics": {"n": 0.7}}

    before_inputs = deepcopy(inputs)
    before_a = deepcopy(layer_a)
    before_b = deepcopy(layer_b)
    before_c = deepcopy(layer_c)
    before_d = deepcopy(layer_d)

    _ = run_alpha_layer_e_signal_interaction_effects(
        signal_inputs=inputs,
        alpha_layer_a_output=layer_a,
        alpha_layer_b_output=layer_b,
        alpha_layer_c_output=layer_c,
        alpha_layer_d_output=layer_d,
    )

    assert inputs == before_inputs
    assert layer_a == before_a
    assert layer_b == before_b
    assert layer_c == before_c
    assert layer_d == before_d


def test_fixed_template_explanation_rule_and_public_api_exports() -> None:
    result = run_alpha_layer_e_signal_interaction_effects(signal_inputs=_base_inputs())
    explanation = result["deterministic_explanation"]
    assert "momentum/breadth condition" in explanation
    assert "valuation/hype pressure" in explanation
    assert "sentiment/transmission condition" in explanation
    assert "divergence/narrative overlap" in explanation
    assert "credit/liquidity condition" in explanation
    assert "concentration/participation risk" in explanation
    assert "final bounded classification=" in explanation
    assert result["classification_rule_applied"].startswith("precedence_")
    assert "interaction_effect_classification" in result
    assert "invariant_flags" in result
