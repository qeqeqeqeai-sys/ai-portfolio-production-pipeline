from transmission_layers.intelligence.tier5.federation_persistence_explanations import fixed_federation_persistence_explanations


def test_fixed_template_stability():
    metrics = {"federation_persistence_score": 0.5}
    assert fixed_federation_persistence_explanations(metrics) == fixed_federation_persistence_explanations(metrics)
