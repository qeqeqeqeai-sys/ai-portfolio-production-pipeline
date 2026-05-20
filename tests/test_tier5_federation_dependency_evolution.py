from transmission_layers.intelligence.tier5.federation_dependency_evolution import federation_dependency_evolution_score


def test_dependency_evolution_bounded():
    assert 0.0 <= federation_dependency_evolution_score([[], [("a", "b")]]) <= 1.0
