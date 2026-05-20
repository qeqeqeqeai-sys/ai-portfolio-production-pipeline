from transmission_layers.intelligence.tier4.reintegration_resistance import score_reintegration_resistance


def test_reintegration_resistance_bounded():
    out = score_reintegration_resistance(0.8, 0.3)
    assert 0.0 <= out["reintegration_resistance_score"] <= 1.0
