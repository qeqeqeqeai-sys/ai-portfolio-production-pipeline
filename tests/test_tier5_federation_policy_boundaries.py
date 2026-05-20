from transmission_layers.intelligence.tier5.federation_policy_boundaries import federation_boundary_enforcement_diagnostics

def test_boundary_score_bounded():
    r = federation_boundary_enforcement_diagnostics([{"bridge_id":"x","boundary_strength":0.1,"minimum_boundary_strength":0.5}])
    assert 0.0 <= r["federation_boundary_enforcement_score"] <= 1.0
