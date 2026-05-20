from transmission_layers.intelligence.tier4.fragility_replay import compare_fragility_replays, replay_fragility


def test_fragility_replay_deterministic_and_comparable():
    seq = [{"system_fragility_score": 0.1}, {"system_fragility_score": 0.2}]
    a = replay_fragility(seq)
    b = replay_fragility(seq)
    assert a["fragility_replay_checksum"] == b["fragility_replay_checksum"]
    cmp_ = compare_fragility_replays(a, b)
    assert cmp_["same_checksum"] is True
