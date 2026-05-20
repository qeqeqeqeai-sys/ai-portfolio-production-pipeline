from transmission_layers.intelligence.tier5.federation_continuity_observability import federation_continuity_observability_diagnostics


def test_continuity_chronology_invariant():
    assert federation_continuity_observability_diagnostics([{"snapshot_id":"1"},{"snapshot_id":"2"}])["federation_continuity_observability_score"] == 1.0
    assert federation_continuity_observability_diagnostics([{"snapshot_id":"2"},{"snapshot_id":"1"}])["federation_continuity_observability_score"] == 0.0
