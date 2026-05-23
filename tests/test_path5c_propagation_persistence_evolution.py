from copy import deepcopy

from transmission_layers.expectation_failure import (
    build_path5a_transmission_graph,
    build_path5b_fragility_propagation_report,
    build_path5c_carrier_persistence,
    build_path5c_corridor_evolution,
    build_path5c_evolution_explainability,
    build_path5c_propagation_persistence_evolution_report,
    build_path5c_propagation_rotation,
    build_path5c_replay_window_index,
    certify_path5c_propagation_persistence_evolution,
)


def _graph_payload(mult=1.0, shift=""):
    nodes = [
        {"node_id": f"n1{shift}", "node_type": "entity", "label": "A", "fragility_score": 80 * mult, "subsector": "software"},
        {"node_id": f"n2{shift}", "node_type": "entity", "label": "B", "fragility_score": 40 * mult, "subsector": "software"},
        {"node_id": f"n3{shift}", "node_type": "entity", "label": "C", "fragility_score": 60 * mult, "subsector": "semis"},
        {"node_id": f"n4{shift}", "node_type": "subsector", "label": "SW", "fragility_score": 30 * mult, "subsector": "software"},
    ]
    edges = [
        {"edge_id": f"e1{shift}", "edge_type": "entity_to_subsector", "source_node_id": f"n1{shift}", "target_node_id": f"n4{shift}", "weight": 100},
        {"edge_id": f"e2{shift}", "edge_type": "entity_to_subsector", "source_node_id": f"n2{shift}", "target_node_id": f"n4{shift}", "weight": 100},
        {"edge_id": f"e3{shift}", "edge_type": "entity_to_theme", "source_node_id": f"n3{shift}", "target_node_id": f"n4{shift}", "weight": 90},
    ]
    g = build_path5a_transmission_graph({"structural_nodes": nodes, "structural_edges": edges})
    g["certification_status"] = "CERTIFIED_TRANSMISSION_GRAPH"
    return g


def _windows():
    r1 = build_path5b_fragility_propagation_report(_graph_payload(1.0, "a"))
    r2 = build_path5b_fragility_propagation_report(_graph_payload(1.1, "b"))
    r3 = build_path5b_fragility_propagation_report(_graph_payload(0.9, "c"))
    return [
        {"window_index": 2, "window_id": "w2", **r2, "source_reference": "p5b:w2"},
        {"window_index": 1, "window_id": "w1", **r1, "source_reference": "p5b:w1"},
        {"window_index": 3, "window_id": "w3", **r3, "source_reference": "p5b:w3"},
    ]


def test_api_export_presence_and_smoke_and_p5b_non_regression():
    report = build_path5c_propagation_persistence_evolution_report(_windows())
    assert "scores" in report and "certification" in report
    assert callable(build_path5b_fragility_propagation_report)


def test_deterministic_checksum_and_immutable_input():
    w = _windows()
    w_copy = deepcopy(w)
    r1 = build_path5c_propagation_persistence_evolution_report(w)
    r2 = build_path5c_propagation_persistence_evolution_report(w)
    assert r1 == r2
    assert r1["report_checksum"] == r2["report_checksum"]
    assert w == w_copy


def test_empty_blocked_single_degraded_multi_certified_and_ordering():
    assert build_path5c_propagation_persistence_evolution_report([])["certification"]["status"] == "BLOCKED_PATH5C_PROPAGATION_PERSISTENCE_EVOLUTION"
    single = build_path5c_propagation_persistence_evolution_report([_windows()[0]])
    assert single["certification"]["status"] == "DEGRADED_PATH5C_PROPAGATION_PERSISTENCE_EVOLUTION"
    multi = build_path5c_propagation_persistence_evolution_report(_windows())
    assert multi["certification"]["status"] == "CERTIFIED_PATH5C_PROPAGATION_PERSISTENCE_EVOLUTION"
    idx = build_path5c_replay_window_index(_windows())["replay_window_index"]
    assert [x["window_id"] for x in idx] == ["w1", "w2", "w3"]


def test_bounded_scores_and_component_methods_and_threshold_behavior():
    report = build_path5c_propagation_persistence_evolution_report(_windows())
    for _k, v in report["scores"].items():
        assert 0 <= v <= 100
    idx = report["replay_window_index"]
    assert "carrier_persistence_score" in build_path5c_carrier_persistence(idx)
    assert "corridor_evolution_score" in build_path5c_corridor_evolution(idx)
    assert "rotation_score" in build_path5c_propagation_rotation(idx)
    assert report["propagation_persistence"]["propagation_broadening_score"] in (0.0, 50.0, 100.0)


def test_explainability_forbidden_language_and_cert_outcomes_and_no_external_behavior():
    report = build_path5c_propagation_persistence_evolution_report(_windows())
    text = report["evolution_explainability"]["narrative"].lower()
    for forbidden in ["will", "likely", "forecast", "predict", "buy", "sell", "outperform", "underperform", "probability", "risk of future"]:
        assert forbidden not in text
    bad = deepcopy(report)
    bad["evolution_explainability"] = build_path5c_evolution_explainability({"rotation_score": 100})
    bad["evolution_explainability"]["forbidden_term_violations"] = ["forecast"]
    assert certify_path5c_propagation_persistence_evolution(_windows(), bad)["status"] == "DEGRADED_PATH5C_PROPAGATION_PERSISTENCE_EVOLUTION"
    assert report["lineage"]["replay_metadata"]["external_calls"] is False
    assert report["lineage"]["replay_metadata"]["runtime_fetches"] is False
