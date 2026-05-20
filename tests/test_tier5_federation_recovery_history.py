from transmission_layers.intelligence.tier5.federation_recovery_history import recovery_dependency_recurrence_score


def test_recovery_recurrence_bounds():
    assert recovery_dependency_recurrence_score([]) == 0.0
    assert 0.0 <= recovery_dependency_recurrence_score([[('a','b')], [('c','d')]]) <= 1.0
