from transmission_layers.intelligence.tier5.federation_boundaries import bridge_boundary_diagnostics

def test_federation_boundaries_contract():
    r = bridge_boundary_diagnostics([{"stability":0.8,"boundary_hardening":0.7,"breach_exposure":0.2}])
    assert 0.0 <= r["bridge_boundary_health_score"] <= 1.0
