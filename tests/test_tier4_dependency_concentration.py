from transmission_layers.intelligence.tier4.dependency_concentration import score_dependency_concentration


def test_dependency_concentration_empty_and_connected():
    assert score_dependency_concentration([])["dependency_concentration_score"] == 0.0
    r = score_dependency_concentration([{"source_node_id": "A"}, {"source_node_id": "A"}, {"source_node_id": "B"}])
    assert r["dependency_concentration_score"] == 0.666667
