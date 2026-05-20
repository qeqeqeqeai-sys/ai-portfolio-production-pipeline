from transmission_layers.intelligence.tier4.structural_entropy import compute_structural_entropy


def test_bounded_entropy_scoring_and_stability():
    s = [{"node_id": "b", "stress": 0.9}, {"node_id": "a", "stress": 0.1}]
    a = compute_structural_entropy(s)
    b = compute_structural_entropy(list(reversed(s)))
    assert 0.0 <= a["entropy_score"] <= 1.0
    assert a["entropy_checksum"] == b["entropy_checksum"]
