from transmission_layers.intelligence.tier5.federation_bottleneck_evolution import federation_bottleneck_evolution_score


def test_bottleneck_evolution_bounded():
    assert 0.0 <= federation_bottleneck_evolution_score([[], ["bn1"]]) <= 1.0
