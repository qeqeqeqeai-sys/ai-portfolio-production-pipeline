from transmission_layers.intelligence.tier4.adaptation_exhaustion import score_adaptation_exhaustion


def test_adaptation_exhaustion_bounded():
    out = score_adaptation_exhaustion(0.7, 0.9)
    assert 0.0 <= out["adaptation_exhaustion_score"] <= 1.0
