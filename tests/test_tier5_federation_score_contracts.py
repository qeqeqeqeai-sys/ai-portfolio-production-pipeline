from transmission_layers.intelligence.tier5.federation_score_contracts import validate_score_contracts


def test_bounded_scores_contract():
    out = validate_score_contracts({"a_score": 0.2, "b_score": 1.2, "x_checksum": "k"})
    assert 0.0 <= out["federation_score_contract_score"] <= 1.0
    assert 0.0 <= out["federation_checksum_contract_score"] <= 1.0
    assert "a_score" in out["bounded_score_keys"]
