from __future__ import annotations

from copy import deepcopy

from transmission_layers.alpha import NARRATIVE_FRAGILITY_CLASSIFICATIONS, run_alpha_layer_d_narrative_fragility


def _base_inputs() -> dict[str, float]:
    return {
        "narrative_strength_score": 0.80,
        "hype_intensity_score": 0.55,
        "sentiment_persistence_score": 0.62,
        "valuation_pressure_score": 0.50,
        "breadth_support_score": 0.76,
        "transmission_quality_score": 0.74,
        "fundamentals_support_score": 0.73,
        "leadership_concentration_score": 0.32,
        "liquidity_support_score": 0.71,
    }


def test_deterministic_repeated_output_and_fingerprint_stability() -> None:
    inputs = _base_inputs()
    one = run_alpha_layer_d_narrative_fragility(narrative_inputs=inputs)
    two = run_alpha_layer_d_narrative_fragility(narrative_inputs=inputs)
    assert one == two
    assert one["replay_metadata"]["fingerprint_sha256"] == two["replay_metadata"]["fingerprint_sha256"]


def test_structurally_supported_narrative() -> None:
    result = run_alpha_layer_d_narrative_fragility(narrative_inputs=_base_inputs())
    assert result["narrative_fragility_classification"] == "structurally_supported_narrative"


def test_overheated_but_supported() -> None:
    result = run_alpha_layer_d_narrative_fragility(
        narrative_inputs={**_base_inputs(), "hype_intensity_score": 0.92, "valuation_pressure_score": 0.90, "sentiment_persistence_score": 0.86}
    )
    assert result["narrative_fragility_classification"] == "overheated_but_supported"


def test_early_narrative_fragility() -> None:
    result = run_alpha_layer_d_narrative_fragility(
        narrative_inputs={**_base_inputs(), "narrative_strength_score": 0.68, "breadth_support_score": 0.60, "transmission_quality_score": 0.58, "fundamentals_support_score": 0.56}
    )
    assert result["narrative_fragility_classification"] == "early_narrative_fragility"


def test_confirmed_narrative_fragility() -> None:
    result = run_alpha_layer_d_narrative_fragility(
        narrative_inputs={
            "narrative_strength_score": 0.90,
            "hype_intensity_score": 1.0,
            "sentiment_persistence_score": 0.90,
            "valuation_pressure_score": 0.90,
            "breadth_support_score": 0.30,
            "transmission_quality_score": 0.30,
            "fundamentals_support_score": 0.30,
            "leadership_concentration_score": 0.50,
            "liquidity_support_score": 0.60,
        }
    )
    assert result["narrative_fragility_classification"] == "confirmed_narrative_fragility"


def test_narrative_exhaustion_risk() -> None:
    result = run_alpha_layer_d_narrative_fragility(
        narrative_inputs={
            "narrative_strength_score": 0.92,
            "hype_intensity_score": 1.0,
            "sentiment_persistence_score": 1.0,
            "valuation_pressure_score": 1.0,
            "breadth_support_score": 0.05,
            "transmission_quality_score": 0.05,
            "fundamentals_support_score": 0.02,
            "leadership_concentration_score": 0.70,
            "liquidity_support_score": 0.10,
        }
    )
    assert result["narrative_fragility_classification"] == "narrative_exhaustion_risk"


def test_speculative_concentration_risk() -> None:
    result = run_alpha_layer_d_narrative_fragility(
        narrative_inputs={
            "narrative_strength_score": 0.60,
            "hype_intensity_score": 0.65,
            "sentiment_persistence_score": 0.58,
            "valuation_pressure_score": 0.60,
            "breadth_support_score": 0.20,
            "transmission_quality_score": 0.20,
            "fundamentals_support_score": 0.22,
            "leadership_concentration_score": 1.0,
            "liquidity_support_score": 0.10,
        }
    )
    assert result["narrative_fragility_classification"] == "speculative_concentration_risk"


def test_invalid_and_insufficient_handling() -> None:
    insufficient = run_alpha_layer_d_narrative_fragility(narrative_inputs={"narrative_strength_score": 0.5})
    assert insufficient["narrative_fragility_classification"] == "insufficient_data"

    invalid = run_alpha_layer_d_narrative_fragility(narrative_inputs={**_base_inputs(), "hype_intensity_score": 1.5})
    assert invalid["narrative_fragility_classification"] == "invalid_input"


def test_bounded_labels_scores_and_component_reconciliation() -> None:
    result = run_alpha_layer_d_narrative_fragility(narrative_inputs=_base_inputs(), alpha_layer_c_output={"classification": "confirmed_divergence"})
    assert result["narrative_fragility_classification"] in NARRATIVE_FRAGILITY_CLASSIFICATIONS

    for key in result["computed_metrics"]:
        assert 0.0 <= result["computed_metrics"][key] <= 1.0

    cmap = result["component_contribution_map"]
    contribution_sum = (
        cmap["narrative_support_gap_contribution"]
        + cmap["sentiment_structure_gap_contribution"]
        + cmap["hype_valuation_gap_contribution"]
        + cmap["concentration_fragility_contribution"]
        + cmap["alpha_layer_c_fragility_penalty"]
    )
    assert round(contribution_sum, 8) == cmap["raw_fragility_score"]
    assert cmap["narrative_fragility_score_clamped"] == result["computed_metrics"]["narrative_fragility_score"]
    assert cmap["reconciliation_residual"] == 0.0


def test_no_input_mutation_including_optional_upstream_outputs() -> None:
    inputs = _base_inputs()
    layer_c = {"classification": "hidden_fragility", "metrics": {"x": 1.0}}
    layer_a = {"classification": "moderate_negative_efficacy"}
    layer_b = {"regime_results": [{"regime_outcome": "fails"}]}

    before_inputs = deepcopy(inputs)
    before_c = deepcopy(layer_c)
    before_a = deepcopy(layer_a)
    before_b = deepcopy(layer_b)

    _ = run_alpha_layer_d_narrative_fragility(
        narrative_inputs=inputs,
        alpha_layer_c_output=layer_c,
        alpha_layer_a_output=layer_a,
        alpha_layer_b_output=layer_b,
    )

    assert inputs == before_inputs
    assert layer_c == before_c
    assert layer_a == before_a
    assert layer_b == before_b


def test_fixed_template_explanation_and_public_api_exports() -> None:
    result = run_alpha_layer_d_narrative_fragility(narrative_inputs=_base_inputs())
    explanation = result["deterministic_explanation"]
    assert "narrative strength=" in explanation
    assert "hype intensity=" in explanation
    assert "valuation pressure=" in explanation
    assert "support quality=" in explanation
    assert "breadth/transmission condition" in explanation
    assert "concentration risk=" in explanation
    assert "final bounded classification=" in explanation
    assert "narrative_fragility_classification" in result
    assert "invariant_flags" in result
