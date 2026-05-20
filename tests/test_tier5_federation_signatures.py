from transmission_layers.intelligence.tier5.federation_signatures import federation_signatures


def test_tier5_federation_signatures_contract():
    result = federation_signatures({"a": 1})
    assert set(result) == {"tier5a_federation_signature", "tier5a_federation_checksum"}
