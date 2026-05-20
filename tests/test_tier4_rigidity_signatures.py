from transmission_layers.intelligence.tier4.rigidity_signatures import compute_rigidity_checksum


def test_rigidity_checksum_stability():
    payload = {"a": 0.123456789, "b": [3, 2, 1], "timestamp": "ignored"}
    c1 = compute_rigidity_checksum(payload)
    c2 = compute_rigidity_checksum(dict(payload))
    assert c1 == c2
