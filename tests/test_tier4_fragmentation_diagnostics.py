from transmission_layers.intelligence.tier4.fragmentation_diagnostics import compute_fragmentation_diagnostics


def test_fragmentation_detection_and_bounds():
    out = compute_fragmentation_diagnostics([{"from": "a", "to": "b", "suppression": 1.0, "stress": 1.0}])
    assert out["fragmentation_detected"] is True
    assert 0.0 <= out["fragmentation_score"] <= 1.0
