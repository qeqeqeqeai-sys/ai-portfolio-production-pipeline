from copy import deepcopy

from transmission_layers.expectation_failure import (
    build_path5a_transmission_graph,
    build_path5b_fragility_propagation_report,
    build_path5b_propagation_foundation,
    certify_path5b_fragility_propagation,
)


def _input_payload():
    nodes = [
        {"node_id": "n1", "node_type": "entity", "label": "A", "fragility_score": 80, "subsector": "software"},
        {"node_id": "n2", "node_type": "entity", "label": "B", "fragility_score": 40, "subsector": "software"},
        {"node_id": "n3", "node_type": "entity", "label": "C", "fragility_score": 60, "subsector": "semis"},
        {"node_id": "n4", "node_type": "subsector", "label": "SW", "fragility_score": 30, "subsector": "software"},
    ]
    edges = [
        {"edge_id": "e1", "edge_type": "entity_to_subsector", "source_node_id": "n1", "target_node_id": "n4", "weight": 100},
        {"edge_id": "e2", "edge_type": "entity_to_subsector", "source_node_id": "n2", "target_node_id": "n4", "weight": 100},
        {"edge_id": "e3", "edge_type": "entity_to_theme", "source_node_id": "n3", "target_node_id": "n4", "weight": 90},
    ]
    g = build_path5a_transmission_graph({"structural_nodes": nodes, "structural_edges": edges})
    g["certification_status"] = "CERTIFIED_TRANSMISSION_GRAPH"
    return g


def test_api_and_export_presence_and_smoke():
    report = build_path5b_fragility_propagation_report(_input_payload())
    assert "foundation" in report and "certification" in report


def test_deterministic_output_checksum_and_immutability():
    payload = _input_payload()
    payload_copy = deepcopy(payload)
    r1 = build_path5b_fragility_propagation_report(payload)
    r2 = build_path5b_fragility_propagation_report(payload)
    assert r1 == r2
    assert r1["report_checksum"] == r2["report_checksum"]
    assert payload == payload_copy


def test_bounded_scores_and_depth_policy_and_attenuation():
    foundation = build_path5b_propagation_foundation(_input_payload())
    assert foundation["propagation_policy"]["max_depth"] == 3
    assert foundation["propagation_policy"]["attenuation_schedule"] == {0: 1.0, 1: 0.6, 2: 0.35, 3: 0.2}
    for n in foundation["node_propagation"]:
        assert 0 <= n["propagation_pressure_score"] <= 100
        d = n["depth_contributions"]
        assert set(d.keys()) == {"depth_0", "depth_1", "depth_2", "depth_3"}


def test_stable_tie_breakers_and_methods_present():
    report = build_path5b_fragility_propagation_report(_input_payload())
    carriers = report["pressure_carriers"]["pressure_carriers"]
    sorted_again = sorted(carriers, key=lambda x: (-x["carrier_load_score"], -x["carrier_breadth_score"], x["node_type"], x["label"], x["node_id"]))
    assert carriers == sorted_again
    assert report["fragility_concentration"]["system_concentration_score"] >= 0
    assert len(report["resilience_corridors"]["resilience_corridors"]) > 0
    assert len(report["pathway_dominance"]["pathway_dominance"]) > 0


def test_explainability_and_certification_states():
    report = build_path5b_fragility_propagation_report(_input_payload())
    text = report["explainability"]["narrative"].lower()
    for forbidden in ["likely", "forecast", "expected return", "buy", "sell", "outperform", "underperform"]:
        assert forbidden not in text
    assert report["certification"]["status"] == "CERTIFIED_PATH5B_FRAGILITY_PROPAGATION"

    degraded = deepcopy(report)
    degraded["explainability"]["forbidden_term_violations"] = ["forecast"]
    cert = certify_path5b_fragility_propagation(_input_payload(), degraded)
    assert cert["status"] == "DEGRADED_PATH5B_FRAGILITY_PROPAGATION"

    blocked = certify_path5b_fragility_propagation({}, report)
    assert blocked["status"] == "BLOCKED_PATH5B_FRAGILITY_PROPAGATION"
