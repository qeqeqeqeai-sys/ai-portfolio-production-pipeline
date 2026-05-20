from transmission_layers.intelligence.tier5.federation_governance_signatures import governance_checksum

def test_checksum_stability_with_rounding():
    a = governance_checksum({"x": 0.123456789}, "p")
    b = governance_checksum({"x": 0.123456781}, "p")
    assert a == b
