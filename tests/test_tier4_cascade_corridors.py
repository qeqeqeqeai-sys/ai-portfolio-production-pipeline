from transmission_layers.intelligence.tier4.cascade_corridors import score_cascade_corridors


def test_corridor_detection_and_determinism():
    edges = [{"source_node_id": "A", "target_node_id": "B", "edge_quality_score": 0.2}, {"source_node_id": "B", "target_node_id": "C", "edge_quality_score": 0.9}]
    stress = {"A": 0.9, "B": 0.8, "C": 0.2}
    r1 = score_cascade_corridors(edges, stress)
    r2 = score_cascade_corridors(list(reversed(edges)), stress)
    assert r1 == r2
    assert r1["corridor_rankings"][0][0] == "A->B"
