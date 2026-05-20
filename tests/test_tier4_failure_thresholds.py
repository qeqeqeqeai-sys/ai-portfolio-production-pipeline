from transmission_layers.intelligence.tier4.failure_thresholds import evaluate_failure_thresholds
from transmission_layers.intelligence.tier4.fragility_analysis import compute_fragility_scores


def test_failure_thresholds_bounded_and_sorted():
    frag = compute_fragility_scores([{"node_id": "z", "overload": 0.9}, {"node_id": "a", "overload": 0.2}])
    out = evaluate_failure_thresholds(frag, threshold=0.3)
    assert 0.0 <= out["failure_threshold"] <= 1.0
    assert out["threshold_breaches"] == sorted(out["threshold_breaches"])
    assert 0.0 <= out["threshold_breach_ratio"] <= 1.0
    assert len(out["node_threshold_statuses"]) == 2
