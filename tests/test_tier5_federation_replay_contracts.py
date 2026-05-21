from transmission_layers.intelligence.tier5.federation_replay_contracts import validate_replay_contract


def test_replay_contract_stable():
    out = validate_replay_contract({"a": 1, "b": [1, 2]})
    assert out["federation_replay_contract_score"] == 1.0
    assert out["federation_determinism_score"] == 1.0
