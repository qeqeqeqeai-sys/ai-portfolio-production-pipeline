from transmission_layers.intelligence.tier4.scenario_signatures import compute_scenario_response_signature


def test_signature_checksum_stability_and_bounds():
    sig1 = compute_scenario_response_signature({"scenario_type": "node_stressed", "target_nodes": ["A"]}, {"dominant_response_factors": ["overload_delta"], "scenario_impact_score": 0.6, "regime_shift_intensity": 0.2}, {"sensitivity_score": 0.5}, {"regime_name": "stressed"})
    sig2 = compute_scenario_response_signature({"scenario_type": "node_stressed", "target_nodes": ["A"]}, {"dominant_response_factors": ["overload_delta"], "scenario_impact_score": 0.6, "regime_shift_intensity": 0.2}, {"sensitivity_score": 0.5}, {"regime_name": "stressed"})
    assert sig1["signature_checksum"] == sig2["signature_checksum"]
    assert 0.0 <= sig1["impact_score"] <= 1.0
