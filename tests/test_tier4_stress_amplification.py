from transmission_layers.intelligence.tier4.stress_amplification import compute_stress_amplification


def test_stress_amplifier_identification():
    out = compute_stress_amplification([
        {"corridor_id": "c2", "entry_stress": 0.3, "exit_stress": 0.8},
        {"corridor_id": "c1", "entry_stress": 0.2, "exit_stress": 0.2},
    ])
    assert out["stress_amplifier_detected"] is True
    assert 0.0 <= out["stress_amplification_score"] <= 1.0
