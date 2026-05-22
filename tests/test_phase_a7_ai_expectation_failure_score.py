from copy import deepcopy

from transmission_layers.expectation_failure import (
    build_ai_expectation_failure_component_contract,
    build_ai_expectation_failure_evidence_summary,
    build_ai_expectation_failure_interaction_rules,
    build_ai_expectation_failure_thresholds,
    build_phase_a7_ai_expectation_failure_report,
    score_ai_expectation_failure,
)


def _payload(**overrides):
    base = {
        "ticker": "NVDA",
        "sector": "Technology",
        "subsector": "Semiconductors",
        "valuation_stretch_score": 70,
        "fundamental_support_score": 60,
        "narrative_saturation_score": 65,
        "certainty_fragility_score": 55,
        "structural_weakness_score": 50,
        "data_quality_flags": ["upstream_ok"],
        "raw_evidence_refs": ["phase_a2", "phase_a3", "phase_a4", "phase_a5", "phase_a6"],
    }
    base.update(overrides)
    return base


def test_public_api_exports_exist():
    assert callable(score_ai_expectation_failure)
    assert callable(build_ai_expectation_failure_thresholds)
    assert callable(build_ai_expectation_failure_component_contract)
    assert callable(build_ai_expectation_failure_interaction_rules)
    assert callable(build_ai_expectation_failure_evidence_summary)
    assert callable(build_phase_a7_ai_expectation_failure_report)


def test_thresholds_and_contract_are_fixed():
    thresholds = build_ai_expectation_failure_thresholds()
    assert thresholds["fallback_missing_or_invalid_score"] == 50
    assert thresholds["interaction_penalty_cap"] == 20
    assert thresholds["component_triggers"] == {
        "elevated_trigger_min": 40,
        "high_trigger_min": 60,
        "severe_trigger_min": 80,
    }
    contract = build_ai_expectation_failure_component_contract()
    assert len(contract["component_scores"]) == 5
    assert set(contract["component_scores"]) == {
        "valuation_stretch_score",
        "fundamental_support_score",
        "narrative_saturation_score",
        "certainty_fragility_score",
        "structural_weakness_score",
    }


def test_interaction_rules_include_all_flags_and_penalties():
    rules = build_ai_expectation_failure_interaction_rules()
    assert set(rules) == {
        "unsupported_valuation_flag",
        "crowded_expectation_flag",
        "certainty_mismatch_flag",
        "structural_confirmation_flag",
        "severe_failure_cluster_flag",
    }
    assert rules["unsupported_valuation_flag"]["penalty"] == 5
    assert rules["crowded_expectation_flag"]["penalty"] == 5
    assert rules["certainty_mismatch_flag"]["penalty"] == 5
    assert rules["structural_confirmation_flag"]["penalty"] == 5
    assert rules["severe_failure_cluster_flag"]["penalty"] == 10


def test_deterministic_output_and_immutable_input():
    payload = _payload()
    before = deepcopy(payload)
    first = score_ai_expectation_failure(payload)
    second = score_ai_expectation_failure(payload)
    assert first == second
    assert payload == before


def test_bounded_scores_and_band_mapping():
    low = score_ai_expectation_failure(_payload(**{k: 0 for k in build_ai_expectation_failure_component_contract()["component_scores"]}))
    high = score_ai_expectation_failure(_payload(**{k: 95 for k in build_ai_expectation_failure_component_contract()["component_scores"]}))
    assert 0 <= low["base_score"] <= 100
    assert 0 <= low["score_value"] <= 100
    assert 0 <= high["base_score"] <= 100
    assert 0 <= high["score_value"] <= 100
    assert low["score_band"] in {"low", "mild"}
    assert high["score_band"] in {"high", "severe"}


def test_missing_and_out_of_range_inputs_handling():
    result = score_ai_expectation_failure(_payload(valuation_stretch_score=None, narrative_saturation_score=200, certainty_fragility_score=-3))
    assert "valuation_stretch_score" in result["missing_inputs"]
    assert result["component_scores"]["valuation_stretch_score"] == 50
    assert result["component_scores"]["narrative_saturation_score"] == 100
    assert result["component_scores"]["certainty_fragility_score"] == 0
    assert "clamped_high:narrative_saturation_score" in result["data_quality_flags"]
    assert "clamped_low:certainty_fragility_score" in result["data_quality_flags"]


def test_interaction_flags_penalty_cap_and_score_equation():
    result = score_ai_expectation_failure(_payload(
        valuation_stretch_score=90,
        fundamental_support_score=90,
        narrative_saturation_score=90,
        certainty_fragility_score=90,
        structural_weakness_score=90,
    ))
    assert all(result["interaction_flags"].values())
    assert result["interaction_penalty"] == 20
    assert result["score_value"] == min(100, result["base_score"] + result["interaction_penalty"])


def test_thresholds_explanation_invariants_and_boundaries():
    result = score_ai_expectation_failure(_payload(valuation_stretch_score=80, fundamental_support_score=70))
    assert isinstance(result["thresholds_triggered"], list)
    assert "interaction_trigger" in result["thresholds_triggered"]
    assert result["explanation_template_id"].startswith("template_ai_expectation_failure_")
    assert "AI Expectation Failure risk is" in result["explanation"]
    required_true = {
        "deterministic_output",
        "replay_compatible",
        "immutable_input_safe",
        "bounded_score",
        "fixed_thresholds_used",
        "fixed_weights_used",
        "fixed_interaction_rules_used",
        "fixed_template_explanation",
        "additive_only_architecture",
        "no_runtime_mutation",
        "no_autonomous_trading",
        "no_prediction_engine",
        "no_optimization_loop",
        "no_adaptive_control",
        "no_component_recomputation",
    }
    assert required_true.issubset({k for k, v in result["invariant_flags"].items() if v})
    report = build_phase_a7_ai_expectation_failure_report()
    boundaries = " ".join(report["implementation_boundaries"])
    assert "no_heatmaps" in boundaries
    assert "no_trading_signals" in boundaries
    assert "no_prediction_engine" in boundaries

