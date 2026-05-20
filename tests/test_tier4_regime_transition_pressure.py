from transmission_layers.intelligence.tier4.regime_transition_pressure import compute_regime_transition_pressure, compute_transition_diagnostics, rank_transition_diagnostics


def test_bounded_transition_pressure_scoring():
    out = compute_regime_transition_pressure([{"node_id": "n1", "stress": 0.9, "overload": 0.8}])
    assert 0.0 <= out["regime_transition_pressure_score"] <= 1.0


def test_transition_diagnostics_deterministic_and_ordered():
    nodes = [{"node_id": "n2", "stress": 0.7, "overload": 0.6, "resilience": 0.2}, {"node_id": "n1", "stress": 0.8, "overload": 0.7, "resilience": 0.8}]
    corridors = [{"from": "n1", "to": "n2", "suppression": 0.9, "stress": 0.9}]
    a = compute_transition_diagnostics(nodes, corridors, transition_id="t1")
    b = compute_transition_diagnostics(list(reversed(nodes)), list(reversed(corridors)), transition_id="t1")
    assert a["transition_checksum"] == b["transition_checksum"]
    ranked = rank_transition_diagnostics([dict(a, transition_id="z"), dict(a, transition_id="a")])
    assert ranked[0]["transition_id"] == "a"
