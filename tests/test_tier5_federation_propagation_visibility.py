from transmission_layers.intelligence.tier5.federation_propagation_visibility import federation_propagation_visibility_diagnostics


def test_propagation_visibility_replay_determinism():
    p=[{"path_id":"p2","source":"B","target":"C","contained":False},{"path_id":"p1","source":"A","target":"B","contained":True}]
    assert federation_propagation_visibility_diagnostics(p)==federation_propagation_visibility_diagnostics(list(reversed(p)))
