from transmission_layers.intelligence.tier4.rigidity_cascades import score_rigidity_cascades


def test_rigidity_cascade_diagnostics():
    out = score_rigidity_cascades([0.8, 0.4], 0.7)
    assert 0.0 <= out["rigidity_cascade_score"] <= 1.0
