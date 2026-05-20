from transmission_layers.intelligence.tier4.persistence_signatures import compute_persistence_signature_checksum


def test_persistence_signature_checksum_stable_with_sorted_payload():
    a = {"b": 2.123456789, "a": 1, "timestamp": "ignored"}
    b = {"a": 1, "b": 2.123456781}
    assert compute_persistence_signature_checksum(a) == compute_persistence_signature_checksum(b)
