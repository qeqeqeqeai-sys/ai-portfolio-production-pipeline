from transmission_layers.intelligence.tier5.federation_temporal_signatures import federation_temporal_checksum, federation_signature_stability


def test_checksum_stability_and_rounding():
    a = {"x": 0.123456789, "y": [2, 1]}
    b = {"y": [2, 1], "x": 0.123456780}
    assert federation_temporal_checksum(a) == federation_temporal_checksum(b)


def test_signature_stability_bounds():
    assert federation_signature_stability([]) == 0.0
    assert 0.0 <= federation_signature_stability(["a", "a", "b"]) <= 1.0
