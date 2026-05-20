from transmission_layers.intelligence.tier4.stress_leakage import compute_stress_leakage


def test_repeated_containment_breach_detection():
    out = compute_stress_leakage([
        {"corridor_id": "a", "exit_stress": 0.9, "containment": 0.2},
        {"corridor_id": "b", "exit_stress": 0.8, "containment": 0.3},
    ])
    assert out["containment_breach_detected"] is True
    assert 0.0 <= out["stress_leakage_score"] <= 1.0
