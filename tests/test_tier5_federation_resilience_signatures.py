from transmission_layers.intelligence.tier5.federation_resilience_signatures import federation_resilience_checksum


def test_checksum_stability_and_rounding():
    a=federation_resilience_checksum({"x":0.12345678,"y":[{"b":2,"a":1}]},"p")
    b=federation_resilience_checksum({"y":[{"a":1,"b":2}],"x":0.12345679},"p")
    assert a==b
