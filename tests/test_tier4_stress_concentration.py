from transmission_layers.intelligence.tier4.stress_concentration import compute_stress_concentration


def test_bounded_stress_concentration_and_immutability():
    nodes = [{"node_id": "b", "stress": 0.9}, {"node_id": "a", "stress": 0.2}]
    original = [dict(x) for x in nodes]
    out = compute_stress_concentration(nodes)
    assert 0.0 <= out["stress_concentration_score"] <= 1.0
    assert 0.0 <= out["bounded_stress_concentration_score"] <= 1.0
    assert nodes == original
