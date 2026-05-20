from transmission_layers.intelligence.tier4.response_policy import generate_structural_response_policy


def test_response_policy_repeatable_and_target_ordering():
    before = {
        "structural_influence_nodes": [
            {"node_id": "B", "traffic_score": 0.9, "fragmentation_score": 0.4, "resilience_score": 0.2, "contagion_score": 0.6},
            {"node_id": "A", "traffic_score": 0.9, "fragmentation_score": 0.4, "resilience_score": 0.2, "contagion_score": 0.6},
        ],
        "quality_scored_edges": [{"source_node_id": "B", "target_node_id": "C", "edge_quality_score": 0.2}, {"source_node_id": "A", "target_node_id": "B", "edge_quality_score": 0.2}],
    }
    after = {"structural_influence_nodes": [{"node_id": "A", "traffic_score": 0.4, "resilience_score": 0.8, "contagion_score": 0.3}], "quality_scored_edges": [{"source_node_id": "A", "target_node_id": "B", "edge_quality_score": 0.8}]}
    p1 = generate_structural_response_policy(before, after, top_k=2)
    p2 = generate_structural_response_policy(before, after, top_k=2)
    assert p1["response_checksum"] == p2["response_checksum"]
    assert p1["target_nodes"][0] == "A"
    assert 0.0 <= p1["bounded_effectiveness_score"] <= 1.0
