from transmission_layers.intelligence.tier4.fragility_analysis import compare_fragility_scores, compute_fragility_scores, summarize_fragility_scores


def test_fragility_scoring_deterministic_bounded_and_tie_order():
    states = [
        {"node_id": "b", "overload": 0.6, "resilience": 0.3, "fragmentation": 0.4, "cascade_amplification": 0.2, "relapse_persistence": 0.4},
        {"node_id": "a", "overload": 0.6, "resilience": 0.3, "fragmentation": 0.4, "cascade_amplification": 0.2, "relapse_persistence": 0.4},
    ]
    out = compute_fragility_scores(states)
    assert out["node_fragility_ranking"][0]["node_id"] == "a"
    assert 0.0 <= out["fragility_score"] <= 1.0
    assert out["fragility_score"] == out["bounded_fragility_score"]
    assert out["fragility_checksum"] == compute_fragility_scores(states)["fragility_checksum"]


def test_fragility_required_fields_present_and_comparable():
    a = compute_fragility_scores([{"node_id": "a", "overload": 0.9, "resilience": 0.1, "fragmentation": 0.8}])
    b = compute_fragility_scores([{"node_id": "b", "overload": 0.1, "resilience": 0.9, "fragmentation": 0.1}])
    for field in [
        "fragility_id",
        "fragility_score",
        "bounded_fragility_score",
        "dominant_fragility_factor",
        "fragility_classification",
        "structural_survivability_score",
        "threshold_proximity_score",
        "fragility_checksum",
    ]:
        assert field in a
    cmp_ = compare_fragility_scores(a, b)
    assert -1.0 <= cmp_["system_fragility_delta"] <= 1.0
    summary = summarize_fragility_scores(a)
    assert summary["fragility_checksum"] == a["fragility_checksum"]
