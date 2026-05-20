from transmission_layers.intelligence.tier4.scenario_replay import replay_scenario_response


def test_replay_chronology_and_checksum_stability():
    seq = [{"scenario_id": "a", "regime_name": "stable", "impact_score": 0.1}, {"scenario_id": "b", "regime_name": "overloaded", "impact_score": 0.7}]
    r1 = replay_scenario_response(seq)
    r2 = replay_scenario_response(seq)
    assert r1["response_timeline"][0]["step"] == 0
    assert r1["scenario_replay_checksum"] == r2["scenario_replay_checksum"]


def test_replay_window_truncation_deterministic():
    seq = [{"scenario_id": "a", "regime_name": "stable", "impact_score": 0.1}, {"scenario_id": "b", "regime_name": "overloaded", "impact_score": 0.7}, {"scenario_id": "c", "regime_name": "fragmented", "impact_score": 0.8}]
    r = replay_scenario_response(seq, window_size=2)
    assert r["scenario_sequence"] == ["a", "b"]
    assert r["replay_consistency_diagnostics"]["chronology_preserved"] is True
