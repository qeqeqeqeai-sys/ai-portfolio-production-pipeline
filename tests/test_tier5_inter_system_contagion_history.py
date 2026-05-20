from transmission_layers.intelligence.tier5.inter_system_contagion_history import contagion_corridor_persistence_score


def test_contagion_recurrence_bounds_disconnected():
    assert contagion_corridor_persistence_score([[], []]) == 0.0
    assert 0.0 <= contagion_corridor_persistence_score([[('a','b')], [('a','b')]]) <= 1.0
