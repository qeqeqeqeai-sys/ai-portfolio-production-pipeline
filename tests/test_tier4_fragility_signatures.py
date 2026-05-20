from transmission_layers.intelligence.tier4.fragility_signatures import (
    compute_fragility_checksum,
    compute_fragility_signature_checksum,
    compute_fragility_signature_id,
    compute_survivability_checksum,
    compute_tipping_point_checksum,
)


def test_fragility_checksum_stable_and_excludes_runtime_keys():
    payload_a = {"a": 1.23456789, "timestamp": "x", "runtime_duration": 999, "items": [{"z": 2}]}
    payload_b = {"items": [{"z": 2}], "a": 1.234567891}
    assert compute_fragility_checksum(payload_a) == compute_fragility_checksum(payload_b)


def test_specific_checksums_and_signature_id_stable():
    payload = {"x": 1, "y": [2, 3]}
    assert compute_tipping_point_checksum(payload) == compute_tipping_point_checksum(payload)
    assert compute_survivability_checksum(payload) == compute_survivability_checksum(payload)
    assert compute_fragility_signature_checksum(payload) == compute_fragility_signature_checksum(payload)
    assert len(compute_fragility_signature_id(payload, length=12)) == 12
