from transmission_layers.intelligence.tier4.recovery_fragments import score_recovery_fragments


def test_recovery_fragmentation_diagnostics():
    edges = [{"source_node_id": "A", "target_node_id": "B"}, {"source_node_id": "B", "target_node_id": "C"}]
    out = score_recovery_fragments(edges, {"A": 0.9, "B": 0.2, "C": 0.1})
    assert out["fragmented_links"]
    assert 0.0 <= out["recovery_fragmentation_score"] <= 1.0
