from transmission_layers.intelligence.tier5.federation_health_explanations import fixed_federation_health_explanations


def test_fixed_template_stability():
    inp={"federation_health_classification":"healthy","federation_structural_health_score":0.8,"diagnostic_readiness_score":0.7,"health_degradation_score":0.2,"dominant_health_factor":"x"}
    a=fixed_federation_health_explanations(inp)
    b=fixed_federation_health_explanations(inp)
    assert a==b
