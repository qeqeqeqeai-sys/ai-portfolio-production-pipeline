from transmission_layers.intelligence.tier4.regime_persistence import compute_regime_persistence, compute_regime_continuity


def snap(d):
    return {"run_date": d, "chokepoint_overload_score": 0.2, "propagated_stress_score": 0.2, "suppression_cascade_score": 0.2, "resilience_degradation_score": 0.2, "corridor_deterioration_score": 0.2, "contagion_escalation_score": 0.2}


def test_identical_snapshots_high_persistence_low_volatility():
    arr = [snap("2026-01-01"), snap("2026-01-02"), snap("2026-01-03")]
    p = compute_regime_persistence(arr)
    assert p["persistence_score"] >= 0.9
    assert p["regime_volatility_score"] <= 0.1


def test_metrics_bounded():
    p = compute_regime_continuity([snap("2026-01-01"), {**snap("2026-01-02"), "chokepoint_overload_score":0.9}])
    for v in p.values():
        assert 0.0 <= v <= 1.0
