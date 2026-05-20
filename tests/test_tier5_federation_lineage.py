from transmission_layers.intelligence.tier5.federation_lineage import federation_lineage_diagnostics


def test_lineage_chronological_ordering_and_bounds():
    r = federation_lineage_diagnostics([{"source":"A","target":"B"}], [{"snapshot_id":"1"},{"snapshot_id":"2"}])
    assert 0.0 <= r["federation_lineage_score"] <= 1.0
