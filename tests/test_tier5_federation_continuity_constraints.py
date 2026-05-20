from transmission_layers.intelligence.tier5.federation_continuity_constraints import federation_continuity_constraint_diagnostics

def test_continuity_chronological_and_stable():
    s = [{"snapshot_id":"2","boundary_weaknesses":["a"]},{"snapshot_id":"1","boundary_weaknesses":["a"]}]
    r = federation_continuity_constraint_diagnostics(s)
    assert r["federation_continuity_constraint_score"] == 1.0
