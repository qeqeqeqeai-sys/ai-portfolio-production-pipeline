from transmission_layers.intelligence.tier4.durability_replay import replay_durability_timeline


def test_durability_replay_deterministic_and_chronological():
    states = [{"node_id": "a", "x": 1}, {"node_id": "b", "x": 2}]
    a = replay_durability_timeline(states)
    b = replay_durability_timeline(states)
    assert a["chronology_preserved"] is True
    assert a["durability_replay_checksum"] == b["durability_replay_checksum"]
