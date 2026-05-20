from transmission_layers.intelligence.tier4.cascade_signatures import compute_cascade_signature_checksum


def test_checksum_stability_and_rounding():
    p1 = {"a": 0.123456789, "b": [2, 1], "timestamp": "ignore"}
    p2 = {"b": [2, 1], "a": 0.123456781}
    assert compute_cascade_signature_checksum(p1) == compute_cascade_signature_checksum(p2)
