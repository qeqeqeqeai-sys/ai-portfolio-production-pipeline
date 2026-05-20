from transmission_layers.intelligence.tier5.federation_bottleneck_persistence import bottleneck_persistence_score


def test_bottleneck_persistence_bounds():
    assert bottleneck_persistence_score([]) == 0.0
    assert 0.0 <= bottleneck_persistence_score([["n1"], ["n1", "n2"]]) <= 1.0
