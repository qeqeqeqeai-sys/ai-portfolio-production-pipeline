from transmission_layers.intelligence.tier4.stabilization_capacity import compute_stabilization_capacity


def _nodes():
    return [
        {"node_id": "b", "overload": 0.8, "resilience": 0.3, "intervention_effectiveness": 0.2, "fragility_score": 0.8},
        {"node_id": "a", "overload": 0.2, "resilience": 0.9, "intervention_effectiveness": 0.8, "fragility_score": 0.1},
    ]


def test_capacity_bounded_and_deterministic_ordering():
    out = compute_stabilization_capacity(_nodes())
    assert 0.0 <= out["stabilization_capacity_score"] <= 1.0
    assert all(0.0 <= r["bounded_capacity_score"] <= 1.0 for r in out["node_capacity_ranking"])
    assert [r["node_id"] for r in out["node_capacity_ranking"]] == ["b", "a"]


def test_capacity_empty_topology():
    out = compute_stabilization_capacity([])
    assert out["node_count"] == 0
    assert out["stabilization_capacity_score"] == 0.0
