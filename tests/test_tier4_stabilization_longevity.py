from transmission_layers.intelligence.tier4.stabilization_longevity import compute_stabilization_longevity


def test_stabilization_longevity_empty_and_disconnected():
    out_empty = compute_stabilization_longevity([])
    assert out_empty["stabilization_longevity_score"] == 0.0
    out = compute_stabilization_longevity([{"node_id": "a", "stable_duration": 0}, {"node_id": "z", "stable_duration": 10}])
    assert out["node_longevity"][0]["node_id"] == "z"
    assert 0.0 <= out["stabilization_longevity_score"] <= 1.0
