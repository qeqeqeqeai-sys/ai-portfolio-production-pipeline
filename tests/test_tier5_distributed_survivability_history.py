from transmission_layers.intelligence.tier5.distributed_survivability_history import survivability_dependency_recurrence_score


def test_survivability_recurrence_bounds():
    assert survivability_dependency_recurrence_score([]) == 0.0
    assert 0.0 <= survivability_dependency_recurrence_score([[('a','b')], [('a','b')]]) <= 1.0
