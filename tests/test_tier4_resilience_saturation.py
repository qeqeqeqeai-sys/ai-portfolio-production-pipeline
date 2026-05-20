from transmission_layers.intelligence.tier4.resilience_saturation import score_resilience_saturation


def test_resilience_saturation_bounded():
    out = score_resilience_saturation(0.2, 0.9)
    assert 0.0 <= out["resilience_saturation_score"] <= 1.0
