from transmission_layers.intelligence.tier5.federation_phase_transitions import federation_phase_transition_score


def test_phase_transitions_bounded():
    assert federation_phase_transition_score([]) == 0.0
    assert federation_phase_transition_score([1]) == 0.0
    assert 0.0 <= federation_phase_transition_score([1, 2, 2, 3]) <= 1.0
