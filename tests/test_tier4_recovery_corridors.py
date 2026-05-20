from transmission_layers.intelligence.tier4.recovery_corridors import score_recovery_corridors


def test_recovery_corridors_deterministic():
    edges = [{"source_node_id": "B", "target_node_id": "C", "edge_quality_score": 0.5}, {"source_node_id": "A", "target_node_id": "B", "edge_quality_score": 0.9}]
    rec = {"A": 0.9, "B": 0.8, "C": 0.2}
    r1 = score_recovery_corridors(edges, rec)
    r2 = score_recovery_corridors(list(reversed(edges)), rec)
    assert r1 == r2
    assert r1["corridor_rankings"][0][0] == "A->B"
