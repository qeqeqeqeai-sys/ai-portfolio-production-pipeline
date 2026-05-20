from transmission_layers.intelligence.tier4.response_replay import replay_structural_response


def test_response_replay_determinism():
    seq = [{"response_policy_id": "r2", "response_type": "x", "response_score": 0.2}, {"response_policy_id": "r1", "response_type": "y", "response_score": 0.3}]
    a = replay_structural_response(seq, window_size=2)
    b = replay_structural_response(seq, window_size=2)
    assert a["response_replay_checksum"] == b["response_replay_checksum"]
    assert a["chronology_preserved"] is True
