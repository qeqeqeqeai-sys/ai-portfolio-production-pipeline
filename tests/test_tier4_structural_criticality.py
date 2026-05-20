from transmission_layers.intelligence.tier4.structural_criticality import score_structural_criticality


def test_structural_criticality_bounded_and_deterministic():
    node = {"node_id": "N1", "influence_score": 0.9, "chokepoint_score": 0.8, "contagion_score": 0.7, "traffic_score": 0.6, "resilience_score": 0.2}
    a = score_structural_criticality(node)
    b = score_structural_criticality(dict(node))
    assert a == b
    assert 0.0 <= a["structural_criticality_score"] <= 1.0
