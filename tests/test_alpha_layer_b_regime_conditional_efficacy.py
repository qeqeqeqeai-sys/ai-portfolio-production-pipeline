from transmission_layers.alpha.layer_b import REGIME_OUTCOMES, run_alpha_layer_b_regime_conditional_signal_efficacy


def test_layer_b_outcomes_and_determinism():
    alpha_outputs = [
        {"signal_name": "s1", "window": "5d", "regime_tag": "risk_on", "classification": "strong_positive_efficacy", "metrics": {"information_coefficient": 0.4, "rank_information_coefficient": 0.3, "factor_decay": 0.02}},
        {"signal_name": "s2", "window": "5d", "regime_tag": "risk_off", "classification": "weak_negative_efficacy", "metrics": {"information_coefficient": -0.1, "rank_information_coefficient": -0.2, "factor_decay": 0.01}},
        {"signal_name": "s3", "window": "5d", "regime_tag": "risk_on", "classification": "moderate_positive_efficacy", "metrics": {"information_coefficient": 0.2, "rank_information_coefficient": 0.2, "factor_decay": 0.2}},
    ]
    regimes = {"risk_on": "expansion", "risk_off": "stress"}
    first = run_alpha_layer_b_regime_conditional_signal_efficacy(alpha_layer_a_outputs=alpha_outputs, regime_classifications=regimes)
    second = run_alpha_layer_b_regime_conditional_signal_efficacy(alpha_layer_a_outputs=alpha_outputs, regime_classifications=regimes)
    assert first == second
    assert first["regime_results"][0]["regime_outcome"] in REGIME_OUTCOMES
    outcomes = {r["signal_name"]: r["regime_outcome"] for r in first["regime_results"]}
    assert outcomes["s1"] == "works"
    assert outcomes["s2"] == "inverts"
    assert outcomes["s3"] == "decays"
