from transmission_layers.intelligence.tier4.reintegration_stability import score_reintegration_stability


def test_reintegration_stability_bounded():
    out = score_reintegration_stability(0.8, 0.2, 0.1)
    assert 0.0 <= out["reintegration_stability_score"] <= 1.0
    assert out["reintegration_stability_detected"] is True
