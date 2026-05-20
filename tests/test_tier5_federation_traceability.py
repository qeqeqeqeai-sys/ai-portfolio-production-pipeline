from transmission_layers.intelligence.tier5.federation_traceability import federation_traceability_diagnostics


def test_traceability_empty_state():
    r = federation_traceability_diagnostics([])
    assert r["federation_traceability_score"] == 0.0
