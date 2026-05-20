from transmission_layers.intelligence.tier5.federation_recovery_evolution import federation_recovery_evolution_score


def test_recovery_evolution_bounded():
    assert 0.0 <= federation_recovery_evolution_score([[], [("a", "b")]]) <= 1.0
