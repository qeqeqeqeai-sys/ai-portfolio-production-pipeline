from transmission_layers.intelligence.tier5.federation_governance_explanations import fixed_federation_governance_explanations

def test_fixed_template_stable():
    a = fixed_federation_governance_explanations({"dominant_governance_factor":"x"})
    b = fixed_federation_governance_explanations({"dominant_governance_factor":"x"})
    assert a == b
