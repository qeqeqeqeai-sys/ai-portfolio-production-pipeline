from copy import deepcopy

from transmission_layers.intelligence.tier4.intervention_strategies import contain_fragmentation, isolate_corridors, reinforce_nodes


def _state():
    return {"structural_influence_nodes": [{"node_id": "B", "resilience_score": 0.2, "traffic_score": 0.9, "contagion_score": 0.8}, {"node_id": "A", "resilience_score": 0.4, "traffic_score": 0.8, "contagion_score": 0.7}], "quality_scored_edges": [{"source_node_id": "A", "target_node_id": "B", "edge_quality_score": 0.2}]}


def test_interventions_are_immutable_and_bounded():
    s = _state(); original = deepcopy(s)
    out = reinforce_nodes(s, ["A"], 0.3)
    assert s == original
    node = [n for n in out["structural_influence_nodes"] if n["node_id"] == "A"][0]
    assert 0.0 <= node["resilience_score"] <= 1.0


def test_empty_and_disconnected_safe():
    assert isolate_corridors({"structural_influence_nodes": [], "quality_scored_edges": []}, ["A->B"])["quality_scored_edges"] == []
    out = contain_fragmentation(_state(), ["X->Y"])
    assert out["quality_scored_edges"]
