from transmission_layers.intelligence.tier4.persistence_durability import compute_persistence_durability


def test_persistence_durability_bounded_and_deterministic():
    states = [
        {"node_id": "b", "resilience_start": 0.9, "resilience_end": 0.6, "volatility": 0.3, "stable_duration": 5},
        {"node_id": "a", "resilience_start": 0.8, "resilience_end": 0.7, "volatility": 0.2, "stable_duration": 6},
    ]
    a = compute_persistence_durability(states)
    b = compute_persistence_durability(states)
    assert 0.0 <= a["durability_score"] <= 1.0
    assert a["durability_score"] == a["bounded_durability_score"]
    assert a["persistence_checksum"] == b["persistence_checksum"]
