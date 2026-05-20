from transmission_layers.intelligence.tier4.causal_replay import replay_causal_influence


def _snapshot(health, stress_a, stress_b):
    return {
        "health_state": health,
        "node_metrics": [
            {"node_id": "A", "propagated_stress": stress_a, "overload": 0.8, "resilience_degradation": 0.7},
            {"node_id": "B", "propagated_stress": stress_b, "overload": 0.3, "resilience_degradation": 0.2},
        ],
        "corridor_metrics": [
            {"corridor_id": "A->B", "source_node_id": "A", "target_node_id": "B", "stress": 0.8, "downstream_overload": 0.6, "resilience_impact": 0.5, "deterioration": 0.6, "state": "degraded"},
            {"corridor_id": "B->A", "source_node_id": "B", "target_node_id": "A", "stress": 0.5, "suppression": 0.7, "downstream_overload": 0.2, "resilience_impact": 0.2, "deterioration": 0.2, "state": "suppressed"},
        ],
    }


def test_causal_replay_shift_and_checksum_stability():
    prev = _snapshot("stressed", 0.6, 0.5)
    cur = _snapshot("fragile", 0.9, 0.2)
    one = replay_causal_influence(prev, cur)
    two = replay_causal_influence(prev, cur)
    assert one == two
    assert one["previous_health_state"] == "stressed"
    assert one["current_health_state"] == "fragile"
    assert one["replay_checksum"]
    assert 0.0 <= one["metrics"]["influence_concentration_score"] <= 1.0


def test_empty_graph_edge_case():
    out = replay_causal_influence({"health_state": "healthy"}, {"health_state": "healthy"})
    assert out["lineage"]["root_cause_nodes"] == []
    assert out["operational_diagnostics"]["causal_path_count"] == 0
