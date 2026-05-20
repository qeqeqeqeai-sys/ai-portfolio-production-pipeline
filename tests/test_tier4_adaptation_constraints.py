from transmission_layers.intelligence.tier4.adaptation_constraints import score_adaptation_constraints


def test_adaptation_constraints_bounded():
    out = score_adaptation_constraints({"node_id": "A", "load_score": 0.9}, [{"A": 0.1}, {"A": 0.1}])
    assert 0.0 <= out["adaptation_constraint_score"] <= 1.0
    assert out["adaptation_constraint_detected"]
