from transmission_layers.intelligence.tier4.propagation_containment import compute_propagation_containment


def test_stress_absorption_vs_transmission_and_disconnected():
    out = compute_propagation_containment([])
    assert out["stress_absorption_score"] == 1.0
    out2 = compute_propagation_containment([{"corridor_id": "x", "containment": 0.8, "exit_stress": 0.2}])
    assert out2["stress_absorption_score"] > out2["stress_transmission_score"]
