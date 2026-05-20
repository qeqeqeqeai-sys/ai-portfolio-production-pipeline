from transmission_layers.intelligence.tier4.response_signatures import compute_response_checksum


def test_response_checksum_stability():
    p = {"x": [1, 2], "y": 0.123456789}
    assert compute_response_checksum(p) == compute_response_checksum(p)
