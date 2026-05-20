from transmission_layers.intelligence.tier4.fragility_signatures import compute_fragility_checksum, compute_fragility_signature_id


def test_fragility_checksum_stable_and_excludes_runtime_keys():
    payload_a = {"a": 1.23456789, "timestamp": "x", "runtime_duration": 999, "items": [{"z": 2}]}
    payload_b = {"items": [{"z": 2}], "a": 1.234567891}
    assert compute_fragility_checksum(payload_a) == compute_fragility_checksum(payload_b)


def test_fragility_signature_id_stable_and_length_bounded():
    payload = {"x": 1, "y": [2, 3]}
    sig = compute_fragility_signature_id(payload, length=12)
    assert len(sig) == 12
    assert sig == compute_fragility_signature_id(payload, length=12)
