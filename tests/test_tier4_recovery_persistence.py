from transmission_layers.intelligence.tier4.recovery_persistence import compute_stabilization_persistence


def test_persistence_bounds_and_classification():
    states = [{"resilience": 0.9, "overload": 0.1}, {"resilience": 0.8, "overload": 0.2}]
    out = compute_stabilization_persistence(states)
    assert 0.0 <= out["persistence_score"] <= 1.0
    assert out["persistence_classification"] in {"stable", "partial", "unbounded"}
