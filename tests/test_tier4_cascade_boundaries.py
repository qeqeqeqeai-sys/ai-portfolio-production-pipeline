from transmission_layers.intelligence.tier4.cascade_boundaries import score_cascade_boundaries


def test_boundary_and_survivability_scores():
    r = score_cascade_boundaries(0.4, 0.3, 0.8)
    assert 0.0 <= r["cascade_boundary_weakness_score"] <= 1.0
    assert 0.0 <= r["local_to_systemic_destabilization_score"] <= 1.0
    assert 0.0 <= r["survivability_continuity_score"] <= 1.0
