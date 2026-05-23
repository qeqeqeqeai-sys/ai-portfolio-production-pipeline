from copy import deepcopy

from transmission_layers import expectation_failure as ef
from transmission_layers.expectation_failure import path5a_structural_transmission_graph as p5a


def _graph():
    return {
        "nodes": [
            {"node_id": "n1", "node_type": "entity", "label": "A", "fragility_score": 95, "subsector": "s1"},
            {"node_id": "n2", "node_type": "entity", "label": "B", "fragility_score": 80, "subsector": "s2"},
            {"node_id": "n3", "node_type": "theme", "label": "C", "fragility_score": 40, "subsector": "s3"},
        ],
        "edges": [
            {"edge_id": "e1", "source_node_id": "n1", "target_node_id": "n2", "edge_type": "entity_to_entity", "weight": 95},
            {"edge_id": "e2", "source_node_id": "n2", "target_node_id": "n3", "edge_type": "entity_to_theme", "weight": 90},
        ],
        "graph_checksum": "g",
        "certification_status": "CERTIFIED_PATH5A_TRANSMISSION_GRAPH",
    }


def _build_p5abcd():
    p5a_payload = _graph()
    p5b = ef.build_path5b_fragility_propagation_report(p5a_payload)
    windows = [{"window_index": 0, "window_id": "w0", **p5b}, {"window_index": 1, "window_id": "w1", **p5b}]
    p5c = ef.build_path5c_propagation_persistence_evolution_report(windows)
    p5d = ef.build_path5d_propagation_regime_classification_report(p5b, p5c)
    return p5a_payload, p5b, p5c, p5d


def test_api_and_export_presence_and_non_regression_smoke():
    for n in [
        "build_path5e_transmission_input_inventory", "build_path5e_supervisor_synthesis", "build_path5e_transmission_state_closeout",
        "build_path5e_supervisor_findings", "build_path5e_governance_boundary_review", "certify_path5e_transmission_state_closeout",
        "build_path5e_propagation_supervisor_closeout_report", "build_path5b_fragility_propagation_report",
        "build_path5c_propagation_persistence_evolution_report", "build_path5d_propagation_regime_classification_report",
    ]:
        assert hasattr(ef, n)
    assert hasattr(p5a, "run_path5a_structural_transmission_graph")


def test_deterministic_repeated_output_checksum_stability_and_immutable_inputs():
    p5a_payload, p5b, p5c, p5d = _build_p5abcd()
    originals = deepcopy((p5a_payload, p5b, p5c, p5d))
    r1 = ef.build_path5e_propagation_supervisor_closeout_report(p5a_payload, p5b, p5c, p5d)
    r2 = ef.build_path5e_propagation_supervisor_closeout_report(p5a_payload, p5b, p5c, p5d)
    assert r1 == r2
    assert r1["manifest_checksum"] == r2["manifest_checksum"]
    assert r1["report_checksum"] == r2["report_checksum"]
    assert (p5a_payload, p5b, p5c, p5d) == originals


def test_missing_partial_blocked_and_certification_outcomes():
    p5a_payload, p5b, p5c, p5d = _build_p5abcd()
    certified = ef.build_path5e_propagation_supervisor_closeout_report(p5a_payload, p5b, p5c, p5d)
    assert certified["transmission_closeout_status"] in {"CERTIFIED_PATH5E_TRANSMISSION_STATE_CLOSEOUT", "DEGRADED_PATH5E_TRANSMISSION_STATE_CLOSEOUT"}
    degraded = ef.build_path5e_propagation_supervisor_closeout_report(p5a_payload, p5b, p5c, {})
    assert degraded["transmission_closeout_status"] == "DEGRADED_PATH5E_TRANSMISSION_STATE_CLOSEOUT"
    blocked = ef.build_path5e_propagation_supervisor_closeout_report({}, p5b, p5c, p5d)
    assert blocked["transmission_closeout_status"] == "BLOCKED_PATH5E_TRANSMISSION_STATE_CLOSEOUT"


def test_fixed_input_order_precedence_state_mapping_findings_and_forbidden_terms():
    p5a_payload, p5b, p5c, p5d = _build_p5abcd()
    r = ef.build_path5e_propagation_supervisor_closeout_report(p5a_payload, p5b, p5c, p5d)
    assert r["input_inventory"]["input_order"] == ["P5-A", "P5-B", "P5-C", "P5-D"]
    assert r["supervisor_transmission_state"] in {
        "CERTIFIED_STABLE_TRANSMISSION_STATE", "CERTIFIED_CONCENTRATED_TRANSMISSION_STATE", "CERTIFIED_CARRIER_DOMINATED_TRANSMISSION_STATE",
        "CERTIFIED_CORRIDOR_WEAKENED_TRANSMISSION_STATE", "CERTIFIED_ROTATING_TRANSMISSION_STATE", "DEGRADED_TRANSMISSION_STATE",
        "BLOCKED_TRANSMISSION_STATE", "INSUFFICIENT_TRANSMISSION_EVIDENCE",
    }
    corpus = " ".join(r["dominant_transmission_findings"]).lower()
    for term in ("will", "likely", "forecast", "predict", "buy", "sell", "probability"):
        assert term not in corpus


def test_governance_boundary_violation_forces_blocked_and_lineage_presence():
    p5a_payload, p5b, p5c, p5d = _build_p5abcd()
    r = ef.build_path5e_transmission_state_closeout(p5a_payload, p5b, p5c, p5d)
    bad = deepcopy(r)
    bad["unsafe"] = "forecast"
    review = ef.build_path5e_governance_boundary_review(bad)
    assert review["status"] == "GOVERNANCE_BOUNDARY_VIOLATION"
    for key in ("p5a_checksum_reference", "p5b_checksum_reference", "p5c_checksum_reference", "p5d_checksum_reference", "synthesis_policy_checksum", "canonical_manifest_checksum", "output_checksum"):
        assert key in r["lineage_summary"]
