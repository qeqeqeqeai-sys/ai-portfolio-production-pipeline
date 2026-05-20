from transmission_layers.intelligence.tier5.federation_boundary_history import boundary_recurrence_score


def test_boundary_recurrence_bounds():
    assert boundary_recurrence_score([]) == 0.0
    assert 0.0 <= boundary_recurrence_score([["x"], ["x", "y"]]) <= 1.0
