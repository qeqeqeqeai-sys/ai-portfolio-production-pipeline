from transmission_layers.intelligence.tier4.flexibility_collapse import score_flexibility_collapse


def test_flexibility_collapse_bounded():
    out = score_flexibility_collapse(0.8, 0.7)
    assert 0.0 <= out["flexibility_collapse_score"] <= 1.0
