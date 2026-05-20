from transmission_layers.intelligence.tier5.inter_system_contagion import contagion_bottleneck_diagnostics


def test_tier5_inter_system_contagion_contract():
    result = contagion_bottleneck_diagnostics([{"contagion_risk": 0.4, "bottleneck_risk": 0.5, "containment": 0.7}])
    assert "inter_system_contagion_risk_score" in result
