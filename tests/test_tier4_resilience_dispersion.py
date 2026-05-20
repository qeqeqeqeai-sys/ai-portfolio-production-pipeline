from transmission_layers.intelligence.tier4.resilience_dispersion import compute_resilience_dispersion


def test_resilience_dispersion_measurement_and_immutable_input():
    nodes = [{"node_id": "a", "resilience": 0.2}, {"node_id": "b", "resilience": 0.8}]
    original = [dict(n) for n in nodes]
    out = compute_resilience_dispersion(nodes)
    assert out["resilience_dispersion_score"] == 0.6
    assert nodes == original
