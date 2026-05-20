from transmission_layers.intelligence.tier4.structural_rigidity import analyze_structural_rigidity


def _sample():
    nodes = [
        {"node_id": "A", "resilience_score": 0.4, "load_score": 0.8},
        {"node_id": "B", "resilience_score": 0.2, "load_score": 0.9},
        {"node_id": "C", "resilience_score": 0.7, "load_score": 0.2},
    ]
    edges = [{"source_node_id": "A", "target_node_id": "B"}, {"source_node_id": "B", "target_node_id": "C"}]
    replay = [{"A": 0.1, "B": 0.4, "C": 0.6}, {"A": 0.2, "B": 0.5, "C": 0.55}, {"A": 0.15, "B": 0.52, "C": 0.57}]
    return nodes, edges, replay


def test_structural_rigidity_bounded_and_deterministic():
    nodes, edges, replay = _sample()
    r1 = analyze_structural_rigidity(nodes, edges, replay)
    r2 = analyze_structural_rigidity(list(reversed(nodes)), list(reversed(edges)), replay)
    assert r1 == r2
    for k, v in r1.items():
        if k.endswith("_score"):
            assert 0.0 <= float(v) <= 1.0


def test_empty_disconnected_and_immutable_input():
    nodes, edges, replay = [{"node_id": "X"}], [], [{"X": 0.1}]
    snap = (list(nodes), list(edges), [dict(x) for x in replay])
    out = analyze_structural_rigidity(nodes, edges, replay)
    assert out["rigidity_replay_window_size"] == 1
    assert nodes == snap[0] and edges == snap[1] and replay == snap[2]
