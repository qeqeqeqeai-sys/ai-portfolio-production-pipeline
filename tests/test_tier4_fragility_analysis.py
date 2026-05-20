from transmission_layers.intelligence.tier4.fragility_analysis import compute_fragility_scores


def test_fragility_scoring_deterministic_bounded_and_tie_order():
    states = [
        {"node_id": "b", "overload": 0.6, "resilience": 0.3, "fragmentation": 0.4, "cascade_amplification": 0.2, "relapse_persistence": 0.4},
        {"node_id": "a", "overload": 0.6, "resilience": 0.3, "fragmentation": 0.4, "cascade_amplification": 0.2, "relapse_persistence": 0.4},
    ]
    a = compute_fragility_scores(states)
    b = compute_fragility_scores(states)
    assert a["fragility_checksum"] == b["fragility_checksum"]
    assert a["node_fragility_ranking"][0]["node_id"] == "a"
    assert 0.0 <= a["system_fragility_score"] <= 1.0
