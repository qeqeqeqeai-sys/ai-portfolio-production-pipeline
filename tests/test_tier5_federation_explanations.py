from transmission_layers.intelligence.tier5.federation_explanations import fixed_template_explanations


def test_tier5_federation_explanations_contract():
    result = fixed_template_explanations({"a_score": 0.5})
    assert set(result) == {"federation_explanation_headline", "federation_explanation_detail"}
