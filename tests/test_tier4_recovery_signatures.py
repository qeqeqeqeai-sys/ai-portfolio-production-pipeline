from transmission_layers.intelligence.tier4.recovery_signatures import compute_recovery_checksum


def test_recovery_checksum_stability_and_exclusions():
    payload = {"a": 0.123456789, "timestamp": "x", "nested": {"duration_ms": 9, "b": 0.5}}
    c1 = compute_recovery_checksum(payload)
    c2 = compute_recovery_checksum({"nested": {"b": 0.5, "duration_ms": 1}, "a": 0.123456781, "timestamp": "y"})
    assert c1 == c2
