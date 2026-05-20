from transmission_layers.intelligence.tier4.survivability_metrics import compute_survivability_metrics


def test_survivability_metrics_bounded_and_irreversibility_flag():
    frag = {"system_fragility_score": 0.9, "node_count": 2}
    thresh = {"threshold_breach_count": 2}
    out = compute_survivability_metrics(frag, thresh)
    assert 0.0 <= out["survivability_score"] <= 1.0
    assert out["cascade_irreversibility_detected"] is True
    assert out["system_stability_band"] in {"low", "moderate", "high"}
