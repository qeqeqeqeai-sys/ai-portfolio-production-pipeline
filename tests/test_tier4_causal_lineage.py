from transmission_layers.intelligence.tier4.causal_lineage import trace_causal_lineage, trace_corridor_lineage, trace_node_lineage


def test_causal_lineage_deterministic_and_cycle_safe():
    node_attr = [
        {"node_id": "A", "attribution_rank": 1, "attribution_reason": "high propagated stress"},
        {"node_id": "B", "attribution_rank": 2, "attribution_reason": "high chokepoint load"},
    ]
    corridor_attr = [
        {"corridor_id": "A->B", "source_node_id": "A", "target_node_id": "B", "attribution_rank": 1, "stress": 0.7, "deterioration": 0.6, "state": "degraded"},
        {"corridor_id": "B->A", "source_node_id": "B", "target_node_id": "A", "attribution_rank": 2, "suppression": 0.8, "state": "suppressed"},
    ]
    first = trace_causal_lineage(node_attr, corridor_attr, max_depth=3)
    second = trace_causal_lineage(node_attr, corridor_attr, max_depth=3)
    assert first == second
    assert first["lineage_checksum"]
    assert first["causal_depth"] <= 3
    assert isinstance(first["suppression_paths"], list)


def test_node_and_corridor_lineage_filters():
    lineage = {
        "causal_paths": [
            {"path": ["A", "B", "C"], "path_type": "amplification", "impact_score": 0.8},
            {"path": ["A", "D"], "path_type": "suppression", "impact_score": 0.4},
        ]
    }
    node = trace_node_lineage("A", lineage)
    corridor = trace_corridor_lineage("A->B", lineage)
    assert node["path_count"] == 2
    assert corridor["path_count"] == 1
