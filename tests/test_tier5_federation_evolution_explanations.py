from transmission_layers.intelligence.tier5.federation_evolution_explanations import fixed_federation_evolution_explanations


def test_explanations_fixed_template():
    r = fixed_federation_evolution_explanations({"topology_evolution_score": 0.1})
    assert "deterministically" in r["federation_evolution_explanation_headline"]
    assert "topology=0.1000" in r["federation_evolution_explanation_detail"]
