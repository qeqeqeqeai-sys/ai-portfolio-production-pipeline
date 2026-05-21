from transmission_layers.intelligence.tier5.federation_health_signatures import federation_health_checksum


def test_checksum_rounding_and_stability():
    assert federation_health_checksum({"x": 0.123456781}, "p") == federation_health_checksum({"x": 0.123456789}, "p")
