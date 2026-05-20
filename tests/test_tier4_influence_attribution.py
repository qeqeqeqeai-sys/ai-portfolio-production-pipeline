from transmission_layers.intelligence.tier4.influence_attribution import (
    attribute_corridor_influence,
    attribute_node_influence,
    compute_structural_influence_summary,
)


def test_node_and_corridor_attribution_is_bounded_and_ranked_stably():
    nodes = [
        {"node_id": "A", "propagated_stress": 0.9, "overload": 0.7, "resilience_degradation": 0.8, "suppression": 0.2, "cascade": 0.5},
        {"node_id": "B", "propagated_stress": 0.9, "overload": 0.7, "resilience_degradation": 0.8, "suppression": 0.2, "cascade": 0.5},
        {"node_id": "C", "propagated_stress": 0.2, "overload": 0.2, "resilience_degradation": 0.2, "suppression": 0.1, "cascade": 0.1},
    ]
    corridors = [
        {"source_node_id": "A", "target_node_id": "B", "stress": 0.8, "downstream_overload": 0.7, "resilience_impact": 0.6, "suppression": 0.1, "cascade": 0.4, "deterioration": 0.7},
        {"source_node_id": "A", "target_node_id": "C", "stress": 0.6, "downstream_overload": 0.4, "resilience_impact": 0.3, "suppression": 0.7, "cascade": 0.1, "deterioration": 0.2},
    ]

    node_attr = attribute_node_influence(nodes)
    corridor_attr = attribute_corridor_influence(corridors)
    assert [n["node_id"] for n in node_attr[:2]] == ["A", "B"]
    assert node_attr[0]["attribution_rank"] == 1
    assert node_attr[1]["attribution_rank"] == 2
    assert all(0.0 <= n["influence_score"] <= 1.0 for n in node_attr)
    assert all(0.0 <= c["influence_score"] <= 1.0 for c in corridor_attr)


def test_influence_summary_has_diagnostics_and_is_deterministic():
    nodes = [{"node_id": "N1", "propagated_stress": 0.5}]
    corridors = []
    first = compute_structural_influence_summary(nodes, corridors)
    second = compute_structural_influence_summary(nodes, corridors)
    assert first == second
    assert first["operational_diagnostics"]["dominant_influence_node"] == "N1"
    assert first["operational_diagnostics"]["attribution_entries"] == 1
