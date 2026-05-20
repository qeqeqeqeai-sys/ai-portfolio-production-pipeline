from transmission_layers.intelligence.tier4.systemic_cascades import build_cascade_intelligence, order_cascades


def _sample():
    return build_cascade_intelligence(
        {"node_id": "A", "influence_score": 0.8, "chokepoint_score": 0.7, "contagion_score": 0.6, "traffic_score": 0.7, "resilience_score": 0.4},
        [{"node_id": "A", "chokepoint_score": 0.7, "traffic_score": 0.8}],
        [{"source_node_id": "A", "target_node_id": "B", "edge_quality_score": 0.4}],
        {"A": 0.8, "B": 0.9},
        0.3,
        0.2,
        0.5,
    )


def test_required_outputs_present_and_bounded():
    c = _sample()
    for k in ["cascade_id","structural_criticality_score","bounded_structural_criticality_score","systemic_cascade_score","cascade_corridor_score","systemic_bottleneck_score","dependency_concentration_score","cascade_boundary_weakness_score","local_to_systemic_destabilization_score","survivability_continuity_score","cascade_escalation_score","dominant_cascade_factor","cascade_classification","cascade_checksum"]:
        assert k in c
    for k, v in c.items():
        if k.endswith("_score"):
            assert 0.0 <= v <= 1.0


def test_tiebreak_ordering():
    a = _sample()
    b = dict(a)
    b["cascade_id"] = "Z"
    ordered = order_cascades([b, a])
    assert ordered[0]["cascade_id"] == "A"
