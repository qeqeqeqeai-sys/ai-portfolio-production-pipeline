from transmission_layers.intelligence.tier4.recovery_replay import replay_structural_recovery, compare_recovery_replays


def test_replay_determinism_and_ordering():
    states = [{"resilience": 0.8}, {"resilience": 0.7}]
    a = replay_structural_recovery(states, window_size=10)
    b = replay_structural_recovery(states, window_size=10)
    cmp_ = compare_recovery_replays(a, b)
    assert a["chronology_preserved"] is True
    assert cmp_["same_checksum"] is True
