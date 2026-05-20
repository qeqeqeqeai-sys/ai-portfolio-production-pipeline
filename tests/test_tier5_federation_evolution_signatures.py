from transmission_layers.intelligence.tier5.federation_evolution_signatures import federation_evolution_checksum


def test_signatures_deterministic_and_rounded():
    a = federation_evolution_checksum({"x": 0.123456789}, prefix="p")
    b = federation_evolution_checksum({"x": 0.123456781}, prefix="p")
    assert a == b
