from transmission_layers.intelligence.tier4.regime_transitions import detect_regime_transition, replay_regime_transitions
from transmission_layers.intelligence.tier4.regime_replay import replay_regime_timeline


def s(d, o):
    return {"run_date": d, "chokepoint_overload_score": o, "propagated_stress_score": o, "suppression_cascade_score": o, "resilience_degradation_score": o, "corridor_deterioration_score": o, "contagion_escalation_score": o}


def test_transition_detection_and_checksum_stability():
    a, b = s("2026-01-01", 0.2), s("2026-01-02", 0.9)
    t1 = detect_regime_transition(a, b)
    t2 = detect_regime_transition(a, b)
    assert t1 == t2
    assert isinstance(t1["transition_checksum"], str)


def test_replay_chronology_and_window_truncation():
    snaps = [s("2026-01-03", 0.3), s("2026-01-01", 0.2), s("2026-01-02", 0.9)]
    transitions = replay_regime_transitions(snaps)
    assert len(transitions) == 2
    replay = replay_regime_timeline(snaps, window_size=2)
    assert replay["regime_replay_window_size"] == 2
