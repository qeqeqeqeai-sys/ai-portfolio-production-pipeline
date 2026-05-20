from transmission_layers.intelligence.tier5.federation_visibility import federation_visibility_diagnostics


def test_visibility_bounds_and_disconnected_handling():
    r = federation_visibility_diagnostics([{"system_id":"A"},{"system_id":"B"}], [])
    assert r["federation_visibility_score"] == 0.0
    assert 0.0 <= r["federation_visibility_gap_score"] <= 1.0
