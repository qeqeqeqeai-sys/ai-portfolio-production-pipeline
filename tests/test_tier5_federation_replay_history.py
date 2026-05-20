from transmission_layers.intelligence.tier5.federation_replay_history import ingest_federation_replay_history


def test_replay_history_deterministic_and_chronological_and_immutable():
    snaps = [{"federation_id": "b", "replay_index": 2, "bridges": [["y", "x"]]}, {"federation_id": "a", "replay_index": 1, "bridges": [["b", "a"]]}]
    original = [dict(x) for x in snaps]
    out1 = ingest_federation_replay_history(snaps)
    out2 = ingest_federation_replay_history(snaps)
    assert out1 == out2
    assert [x["replay_index"] for x in out1] == [1, 2]
    assert snaps == original
