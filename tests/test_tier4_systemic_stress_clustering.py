from transmission_layers.intelligence.tier4.systemic_stress_clustering import compute_systemic_stress_clustering


def test_systemic_stress_clustering_detection():
    out = compute_systemic_stress_clustering([{"node_id": "a", "stress": 0.8}, {"node_id": "b", "stress": 0.9}, {"node_id": "c", "stress": 0.1}])
    assert out["systemic_stress_cluster_detected"] is True
    assert 0.0 <= out["systemic_stress_clustering_score"] <= 1.0
