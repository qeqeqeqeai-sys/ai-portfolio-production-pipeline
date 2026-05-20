from transmission_layers.intelligence.tier4.resistance_signatures import compute_capacity_checksum, compute_resistance_signature_checksum


def test_checksum_stability_and_rounding():
    a = {"x": 0.1234567, "timestamp": "ignore"}
    b = {"x": 0.12345671}
    assert compute_capacity_checksum(a) == compute_capacity_checksum(b)
    assert compute_resistance_signature_checksum({"k": [1, 2]}) == compute_resistance_signature_checksum({"k": [1, 2]})
