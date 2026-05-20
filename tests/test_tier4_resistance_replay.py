from transmission_layers.intelligence.tier4.resistance_replay import replay_resistance_timeline


def test_replay_determinism_and_empty():
    states = [{"node": "a"}, {"node": "b"}]
    a = replay_resistance_timeline(states, window_size=2)
    b = replay_resistance_timeline(states, window_size=2)
    assert a == b
    assert replay_resistance_timeline([], window_size=5)["resistance_replay_window_size"] == 0
