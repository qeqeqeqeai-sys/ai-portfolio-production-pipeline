from transmission_layers.intelligence.tier4.response_effectiveness import compute_response_effectiveness


def test_effectiveness_bounds_and_checksum_stability():
    before = {"structural_influence_nodes": [{"traffic_score": 0.9, "resilience_score": 0.2, "contagion_score": 0.8}], "quality_scored_edges": [{"edge_quality_score": 0.2}]}
    after = {"structural_influence_nodes": [{"traffic_score": 0.6, "resilience_score": 0.5, "contagion_score": 0.3}], "quality_scored_edges": [{"edge_quality_score": 0.6}]}
    a = compute_response_effectiveness(before, after)
    b = compute_response_effectiveness(before, after)
    assert a["response_effectiveness_checksum"] == b["response_effectiveness_checksum"]
    assert 0.0 <= a["response_effectiveness_score"] <= 1.0
    assert all(-1.0 <= v <= 1.0 for v in a["effectiveness_deltas"].values())
