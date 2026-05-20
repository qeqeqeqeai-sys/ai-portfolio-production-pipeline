from transmission_layers.intelligence.tier4.contagion_boundaries import compute_contagion_boundaries


def test_bounded_boundary_score_and_empty_topology():
    out = compute_contagion_boundaries([])
    assert out["contagion_boundary_detected"] is True
    out2 = compute_contagion_boundaries([{"corridor_id": "x", "containment": 0.1}])
    assert 0.0 <= out2["contagion_boundary_score"] <= 1.0
