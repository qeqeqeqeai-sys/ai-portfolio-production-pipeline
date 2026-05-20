from transmission_layers.intelligence.tier5.federation_signatures import federation_signatures

def test_federation_signatures_contract():
    r = federation_signatures({"a":1})
    assert set(r) == {"tier5a_federation_signature","tier5a_federation_checksum"}
