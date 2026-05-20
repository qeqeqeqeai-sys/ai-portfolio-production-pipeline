from transmission_layers.intelligence.tier4.structural_regimes import TIE_PRIORITY, classify_structural_regime, compare_regime_states


def _snap(**kw):
    base = {"propagated_stress_score":0.3,"chokepoint_overload_score":0.3,"suppression_cascade_score":0.3,"resilience_degradation_score":0.3,"corridor_deterioration_score":0.3,"contagion_escalation_score":0.3,"overloaded_nodes":[],"degraded_corridors":[],"suppressed_corridors":[],"failed_corridors":[]}
    base.update(kw)
    return base


def test_regime_classification_deterministic_and_bounded():
    s = _snap(chokepoint_overload_score=0.9)
    a = classify_structural_regime(s)
    b = classify_structural_regime(s)
    assert a == b
    assert 0.0 <= a["regime_score"] <= 1.0


def test_tie_breaking_equal_scores():
    s = _snap(chokepoint_overload_score=0.8, suppression_cascade_score=0.8, propagated_stress_score=0.8)
    expected = min({"cascading_failure", "overloaded"}, key=TIE_PRIORITY.index)
    for _ in range(5):
        assert classify_structural_regime(s)["regime_name"] == expected


def test_classification_clamps_out_of_range_scores_and_checksum_is_stable():
    s = _snap(
        chokepoint_overload_score=3.0,
        suppression_cascade_score=-2.0,
        propagated_stress_score=99.0,
        resilience_degradation_score=-5.0,
    )
    a = classify_structural_regime(s)
    b = classify_structural_regime(s)
    assert a["regime_checksum"] == b["regime_checksum"]
    assert 0.0 <= a["regime_score"] <= 1.0


def test_fragmented_recovering_overloaded_suppressed_detection():
    assert classify_structural_regime(_snap(corridor_deterioration_score=0.9, resilience_degradation_score=0.9))["regime_name"] == "fragmented"
    assert classify_structural_regime(_snap(chokepoint_overload_score=0.95))["regime_name"] == "overloaded"
    assert classify_structural_regime(_snap(suppression_cascade_score=0.95))["regime_name"] in {"suppressed", "cascading_failure"}
    assert classify_structural_regime(_snap(chokepoint_overload_score=0.1, suppression_cascade_score=0.1, corridor_deterioration_score=0.1))["regime_name"] in {"recovering","stable"}


def test_compare_states():
    c = compare_regime_states(_snap(), _snap(chokepoint_overload_score=0.9))
    assert c["regime_changed"] is True
