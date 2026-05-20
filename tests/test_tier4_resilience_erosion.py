from transmission_layers.intelligence.tier4.resilience_erosion import compute_resilience_erosion


def test_resilience_erosion_detection_and_stability():
    out = compute_resilience_erosion([
        {"node_id": "x", "resilience_start": 1.0, "resilience_end": 0.5},
        {"node_id": "a", "resilience_start": 0.2, "resilience_end": 0.2},
    ])
    assert 0.0 <= out["resilience_erosion_score"] <= 1.0
    assert out["node_erosion"][0]["node_id"] == "x"
    assert out["erosion_checksum"] == compute_resilience_erosion([
        {"node_id": "x", "resilience_start": 1.0, "resilience_end": 0.5},
        {"node_id": "a", "resilience_start": 0.2, "resilience_end": 0.2},
    ])["erosion_checksum"]
