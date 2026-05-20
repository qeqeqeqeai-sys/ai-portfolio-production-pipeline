from transmission_layers.intelligence.tier5.federation_replay_observability import federation_replay_observability_diagnostics


def test_replay_observability_checksum_stability():
    r1 = federation_replay_observability_diagnostics([{"snapshot_id":"1"}])
    r2 = federation_replay_observability_diagnostics([{"snapshot_id":"1"}])
    assert r1 == r2
