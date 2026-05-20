from transmission_layers.intelligence.tier4.recovery_signatures import compute_recovery_checksum


def test_recovery_checksum_stable_and_excludes_runtime_keys():
    payload_a = {"a": 1.23456789, "timestamp": "x", "runtime_duration": 999, "items": [{"z": 2}]}
    payload_b = {"items": [{"z": 2}], "a": 1.234567891}
    assert compute_recovery_checksum(payload_a) == compute_recovery_checksum(payload_b)
