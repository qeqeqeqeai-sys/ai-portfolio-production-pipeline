from transmission_layers.intelligence.tier5.federation_constraint_history import federation_constraint_history_diagnostics

def test_constraint_history_recurrence():
    r = federation_constraint_history_diagnostics([{"snapshot_id":"1","boundary_weaknesses":["a"]},{"snapshot_id":"2","boundary_weaknesses":["b"]}])
    assert r["federation_constraint_recurrence_score"] == 1.0
