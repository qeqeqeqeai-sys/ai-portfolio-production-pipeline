from transmission_layers.intelligence.tier4.recovery_decay import compute_recovery_decay, detect_structural_relapse


def test_decay_and_relapse_detection_stable():
    states = [
        {"resilience": 0.9, "overload": 0.1, "fragmentation": 0.1},
        {"resilience": 0.6, "overload": 0.3, "fragmentation": 0.2},
    ]
    decay = compute_recovery_decay(states)
    relapse = detect_structural_relapse(states)
    assert decay["dominant_decay_factor"] in {"resilience", "overload", "fragmentation", "none"}
    assert 0.0 <= relapse["relapse_score"] <= 1.0
