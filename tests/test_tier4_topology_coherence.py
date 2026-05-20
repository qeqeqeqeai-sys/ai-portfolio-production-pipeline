from transmission_layers.intelligence.tier4.topology_coherence import compute_topology_coherence


def test_empty_and_disconnected_topology_handling():
    assert compute_topology_coherence([], [])["topology_coherence_score"] == 1.0
    out = compute_topology_coherence([{"node_id": "n1"}, {"node_id": "n2"}], [])
    assert out["topology_coherence_degradation_detected"] is True
