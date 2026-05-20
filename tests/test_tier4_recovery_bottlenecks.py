from transmission_layers.intelligence.tier4.recovery_bottlenecks import score_recovery_bottlenecks


def test_recovery_bottlenecks_identification():
    nodes = [{"node_id": "A", "chokepoint_score": 0.1}, {"node_id": "B", "chokepoint_score": 0.8}]
    out = score_recovery_bottlenecks(nodes, {"A": 0.9, "B": 0.1})
    assert out["node_bottlenecks"][1][0] == "B"
    assert 0.0 <= out["recovery_bottleneck_score"] <= 1.0
