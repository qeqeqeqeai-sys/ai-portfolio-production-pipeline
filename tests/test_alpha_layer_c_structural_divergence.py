from __future__ import annotations

from copy import deepcopy

from transmission_layers.alpha import DIVERGENCE_CLASSIFICATIONS, run_alpha_layer_c_structural_divergence_intelligence


def _base_inputs() -> dict[str, float]:
    return {
        "index_strength_score": 0.82,
        "breadth_support_score": 0.74,
        "leadership_concentration_score": 0.30,
        "cross_asset_confirmation_score": 0.77,
        "transmission_consistency_score": 0.79,
    }


def test_deterministic_repeated_output_and_fingerprint_stability() -> None:
    inputs = _base_inputs()
    one = run_alpha_layer_c_structural_divergence_intelligence(structural_inputs=inputs)
    two = run_alpha_layer_c_structural_divergence_intelligence(structural_inputs=inputs)
    assert one == two
    assert one["replay_metadata"]["fingerprint_sha256"] == two["replay_metadata"]["fingerprint_sha256"]


def test_hidden_fragility_detection() -> None:
    result = run_alpha_layer_c_structural_divergence_intelligence(
        structural_inputs={
            "index_strength_score": 0.92,
            "breadth_support_score": 0.10,
            "leadership_concentration_score": 0.96,
            "cross_asset_confirmation_score": 0.22,
            "transmission_consistency_score": 0.24,
        }
    )
    assert result["classification"] == "hidden_fragility"


def test_early_divergence_detection() -> None:
    result = run_alpha_layer_c_structural_divergence_intelligence(
        structural_inputs={
            "index_strength_score": 0.66,
            "breadth_support_score": 0.62,
            "leadership_concentration_score": 0.42,
            "cross_asset_confirmation_score": 0.68,
            "transmission_consistency_score": 0.70,
        }
    )
    assert result["classification"] == "early_divergence"


def test_confirmed_divergence_detection() -> None:
    result = run_alpha_layer_c_structural_divergence_intelligence(
        structural_inputs={
            "index_strength_score": 0.86,
            "breadth_support_score": 0.35,
            "leadership_concentration_score": 0.78,
            "cross_asset_confirmation_score": 0.40,
            "transmission_consistency_score": 0.40,
        }
    )
    assert result["classification"] == "confirmed_divergence"


def test_invalid_and_insufficient_handling() -> None:
    insufficient = run_alpha_layer_c_structural_divergence_intelligence(structural_inputs={"index_strength_score": 0.9})
    assert insufficient["classification"] == "insufficient_data"

    invalid = run_alpha_layer_c_structural_divergence_intelligence(
        structural_inputs={
            "index_strength_score": 1.2,
            "breadth_support_score": 0.5,
            "leadership_concentration_score": 0.5,
            "cross_asset_confirmation_score": 0.5,
            "transmission_consistency_score": 0.5,
        }
    )
    assert invalid["classification"] == "invalid_input"


def test_bounded_labels() -> None:
    result = run_alpha_layer_c_structural_divergence_intelligence(structural_inputs=_base_inputs())
    assert result["classification"] in DIVERGENCE_CLASSIFICATIONS


def test_no_input_mutation() -> None:
    structural_inputs = _base_inputs()
    alpha_a = {"classification": "strong_negative_efficacy", "metrics": {"x": 1}}
    alpha_b = {"regime_results": [{"regime_outcome": "fails"}, {"regime_outcome": "works"}]}

    before_structural = deepcopy(structural_inputs)
    before_a = deepcopy(alpha_a)
    before_b = deepcopy(alpha_b)

    _ = run_alpha_layer_c_structural_divergence_intelligence(
        structural_inputs=structural_inputs,
        alpha_layer_a_output=alpha_a,
        alpha_layer_b_output=alpha_b,
    )

    assert structural_inputs == before_structural
    assert alpha_a == before_a
    assert alpha_b == before_b


def test_public_api_exports() -> None:
    assert "hidden_fragility" in DIVERGENCE_CLASSIFICATIONS
    result = run_alpha_layer_c_structural_divergence_intelligence(structural_inputs=_base_inputs())
    assert "component_contribution_map" in result
    assert "invariant_flags" in result


def test_scores_bounded_and_reconciled() -> None:
    result = run_alpha_layer_c_structural_divergence_intelligence(
        structural_inputs={
            "index_strength_score": 1.0,
            "breadth_support_score": 0.0,
            "leadership_concentration_score": 1.0,
            "cross_asset_confirmation_score": 0.0,
            "transmission_consistency_score": 0.0,
        },
        alpha_layer_a_output={"classification": "strong_negative_efficacy"},
        alpha_layer_b_output={"regime_results": [{"regime_outcome": "fails"}] * 5},
    )

    assert 0.0 <= result["metrics"]["divergence_score"] <= 1.0
    assert 0.0 <= result["metrics"]["fragility_score"] <= 1.0

    cmap = result["component_contribution_map"]
    contribution_sum = (
        cmap["index_strength_contribution"]
        + cmap["breadth_deterioration_contribution"]
        + cmap["leadership_concentration_contribution"]
        + cmap["cross_asset_disagreement_contribution"]
        + cmap["transmission_inconsistency_contribution"]
        + cmap["alpha_layer_a_penalty"]
        + cmap["alpha_layer_b_penalty"]
    )
    assert round(contribution_sum, 8) == cmap["raw_divergence_score"]
    assert cmap["divergence_score_clamped"] == result["metrics"]["divergence_score"]
    assert cmap["reconciliation_residual"] == 0.0
