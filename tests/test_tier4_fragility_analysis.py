from transmission_layers.intelligence.tier4.fragility_analysis import (
    compare_fragility_scores,
    compute_fragility_scores,
    summarize_fragility_scores,
)


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


def test_fragility_summary_and_comparison():
    a = compute_fragility_scores([{"node_id": "a", "overload": 0.9, "resilience": 0.1, "fragmentation": 0.8}])
    b = compute_fragility_scores([{"node_id": "b", "overload": 0.2, "resilience": 0.9, "fragmentation": 0.2}])
    cmp_ = compare_fragility_scores(a, b)
    summary = summarize_fragility_scores(a)
    assert -1.0 <= cmp_["system_fragility_delta"] <= 1.0
    assert summary["top_fragility_node"] == "a"
