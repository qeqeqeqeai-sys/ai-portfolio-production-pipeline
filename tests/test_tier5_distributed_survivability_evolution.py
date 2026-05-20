from transmission_layers.intelligence.tier5.distributed_survivability_evolution import distributed_survivability_evolution_score


def test_survivability_evolution_bounded():
    assert 0.0 <= distributed_survivability_evolution_score([[], [("a", "b")]]) <= 1.0
