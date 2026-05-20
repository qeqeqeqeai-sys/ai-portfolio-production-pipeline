from transmission_layers.intelligence.tier4.scenario_sensitivity import compute_structural_sensitivity_summary


def test_sensitivity_bounded_and_stable():
    b = {"stressed_nodes": ["A"], "degraded_corridors": ["A->B"], "suppressed_corridors": [], "failed_corridors": []}
    c = {"stressed_nodes": ["A", "B"], "degraded_corridors": [], "suppressed_corridors": ["A->B"], "failed_corridors": []}
    s1 = compute_structural_sensitivity_summary(b, c)
    s2 = compute_structural_sensitivity_summary(b, c)
    assert 0.0 <= s1["sensitivity_score"] <= 1.0
    assert s1 == s2
