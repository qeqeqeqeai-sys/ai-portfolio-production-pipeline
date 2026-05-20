from transmission_layers.intelligence.tier4.chronic_instability import compute_chronic_instability


def test_chronic_instability_detected_and_bounded():
    out = compute_chronic_instability([{"node_id": "a", "volatility": 0.9}, {"node_id": "b", "volatility": 0.1}])
    assert 0.0 <= out["chronic_instability_score"] <= 1.0
    assert out["chronic_instability_detected"] is True
    assert out["instability_checksum"]
