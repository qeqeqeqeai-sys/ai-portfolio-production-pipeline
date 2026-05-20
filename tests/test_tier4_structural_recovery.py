from transmission_layers.intelligence.tier4.structural_recovery import analyze_structural_recovery


def _sample():
    nodes = [{"node_id": "A", "chokepoint_score": 0.2}, {"node_id": "B", "chokepoint_score": 0.9}, {"node_id": "C", "chokepoint_score": 0.5}]
    edges = [{"source_node_id": "A", "target_node_id": "B", "edge_quality_score": 0.9}, {"source_node_id": "B", "target_node_id": "C", "edge_quality_score": 0.6}]
    replay = [{"A": 0.2, "B": 0.1, "C": 0.3}, {"A": 0.5, "B": 0.4, "C": 0.45}, {"A": 0.7, "B": 0.55, "C": 0.6}]
    return nodes, edges, replay


def test_recovery_outputs_bounded_and_stable():
    nodes, edges, replay = _sample()
    r1 = analyze_structural_recovery(nodes, edges, replay)
    r2 = analyze_structural_recovery(list(reversed(nodes)), list(reversed(edges)), replay)
    assert r1 == r2
    for k, v in r1.items():
        if k.endswith("_score"):
            assert 0.0 <= float(v) <= 1.0
    assert r1["recovery_checksum"]


def test_empty_and_disconnected_handling_and_immutable_input():
    nodes = [{"node_id": "X", "chokepoint_score": 0.0}]
    edges = []
    replay = [{"X": 0.0}, {"X": 0.1}]
    snapshot = (list(nodes), list(edges), [dict(x) for x in replay])
    out = analyze_structural_recovery(nodes, edges, replay)
    assert out["recovery_replay_window_size"] == 2
    assert nodes == snapshot[0] and edges == snapshot[1] and replay == snapshot[2]
