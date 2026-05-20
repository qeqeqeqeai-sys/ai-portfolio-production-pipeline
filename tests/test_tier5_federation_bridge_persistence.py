from transmission_layers.intelligence.tier5.federation_bridge_persistence import bridge_persistence_score


def test_bridge_persistence_bounds_and_single_snapshot():
    assert bridge_persistence_score([]) == 0.0
    assert bridge_persistence_score([[('a','b')]]) == 1.0
    assert 0.0 <= bridge_persistence_score([[('a','b')], [('a','b'),('b','c')]]) <= 1.0
