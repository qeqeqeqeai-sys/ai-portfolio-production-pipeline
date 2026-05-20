from transmission_layers.intelligence.tier4.systemic_bottlenecks import score_systemic_bottlenecks


def test_bottleneck_identification_disconnected():
    nodes = [{"node_id": "A", "chokepoint_score": 1.0, "traffic_score": 1.0}, {"node_id": "B", "chokepoint_score": 0.0, "traffic_score": 0.0}]
    r = score_systemic_bottlenecks(nodes, {"A": 1.0, "B": 0.0})
    assert 0 <= r["systemic_bottleneck_score"] <= 1
