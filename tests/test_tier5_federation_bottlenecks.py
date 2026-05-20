from transmission_layers.intelligence.tier5.federation_bottlenecks import contagion_bottleneck_diagnostics


def test_tier5_federation_bottlenecks_contract():
    result = contagion_bottleneck_diagnostics([{"contagion_risk": 0.4, "bottleneck_risk": 0.5, "containment": 0.7}])
    assert "federation_bottleneck_risk_score" in result
