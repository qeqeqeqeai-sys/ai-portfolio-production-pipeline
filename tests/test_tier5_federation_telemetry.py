from transmission_layers.intelligence.tier5.federation_telemetry import federation_telemetry_diagnostics


def test_telemetry_bounds():
    r = federation_telemetry_diagnostics([{"snapshot_id":"1","x":1},{"snapshot_id":"2"}])
    assert 0.0 <= r["federation_telemetry_score"] <= 1.0
