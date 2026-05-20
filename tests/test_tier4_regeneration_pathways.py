from transmission_layers.intelligence.tier4.regeneration_pathways import score_regeneration_pathways


def test_regeneration_pathways_analysis():
    nodes = [{"node_id": "A"}, {"node_id": "B"}]
    replay = [{"A": 0.1, "B": 0.3}, {"A": 0.3, "B": 0.2}, {"A": 0.7, "B": 0.5}]
    out = score_regeneration_pathways(nodes, replay)
    assert 0.0 <= out["regeneration_pathway_score"] <= 1.0
    assert out["node_regeneration"][0][0] == "A"
