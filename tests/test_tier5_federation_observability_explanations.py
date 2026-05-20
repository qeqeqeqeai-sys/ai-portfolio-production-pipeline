from transmission_layers.intelligence.tier5.federation_observability_explanations import fixed_federation_observability_explanations


def test_observability_explanations_fixed_template():
    e = fixed_federation_observability_explanations({"dominant_observability_factor": "federation_traceability_score"})
    assert "Deterministic distributed observability" in e["federation_observability_explanation"]
    assert "federation_traceability_score" in e["federation_observability_dominant_factor_explanation"]
