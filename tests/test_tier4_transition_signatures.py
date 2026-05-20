from transmission_layers.intelligence.tier4.transition_signatures import compute_transition_checksum, compute_transition_signature_checksum


def test_checksum_stability_and_rounding():
    a = {"x": 0.12345678, "runtime_duration": 10}
    b = {"x": 0.12345679, "runtime_duration": 20}
    assert compute_transition_checksum(a) == compute_transition_checksum(b)
    assert compute_transition_signature_checksum({"k": [2, 1]}) == compute_transition_signature_checksum({"k": [2, 1]})
