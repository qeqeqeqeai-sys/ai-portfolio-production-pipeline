from transmission_layers.intelligence.tier4.regime_state_machine import validate_regime_transition, enumerate_allowed_transitions, compute_transition_path


def test_allowed_transition_validation_and_rejection():
    assert validate_regime_transition("stable", "stressed")["valid"] is True
    assert validate_regime_transition("stable", "cascading_failure")["valid"] is False


def test_transition_path_computation_bounded():
    p = compute_transition_path("stable", "cascading_failure", max_depth=6)
    assert p["path_found"] is True
    assert p["path"][0] == "stable"


def test_transition_ordering_stable():
    m = enumerate_allowed_transitions()
    assert list(m.keys()) == sorted(m.keys())
