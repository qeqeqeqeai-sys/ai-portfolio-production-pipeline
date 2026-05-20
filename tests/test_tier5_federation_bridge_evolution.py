from transmission_layers.intelligence.tier5.federation_bridge_evolution import federation_bridge_evolution_score


def test_bridge_evolution_bounded():
    assert 0.0 <= federation_bridge_evolution_score([[], [("a", "b")]]) <= 1.0
