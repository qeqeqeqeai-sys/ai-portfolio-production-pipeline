from transmission_layers.intelligence.tier5.federation_explanations import fixed_template_explanations

def test_federation_explanations_contract():
    r = fixed_template_explanations({"a_score":0.5})
    assert set(r) == {"federation_explanation_headline","federation_explanation_detail"}
