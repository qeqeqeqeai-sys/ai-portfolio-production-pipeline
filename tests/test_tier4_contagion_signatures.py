from transmission_layers.intelligence.tier4.contagion_signatures import (
    compute_contagion_checksum,
    compute_contagion_signature_checksum,
)


def test_checksum_stability_determinism_and_rounding():
    a = {"x": 0.12345678, "timestamp": "ignore", "k": [{"b": 2, "a": 1}]}
    b = {"x": 0.12345679, "timestamp": "other", "k": [{"a": 1, "b": 2}]}
    assert compute_contagion_checksum(a) == compute_contagion_checksum(b)
    assert compute_contagion_signature_checksum({"z": [2, 1]}) == compute_contagion_signature_checksum({"z": [2, 1]})
