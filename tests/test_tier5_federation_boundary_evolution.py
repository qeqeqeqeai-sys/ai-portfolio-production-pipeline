from transmission_layers.intelligence.tier5.federation_boundary_evolution import federation_boundary_evolution_score


def test_boundary_evolution_bounded():
    assert 0.0 <= federation_boundary_evolution_score([[], ["x"]]) <= 1.0
