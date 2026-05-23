from copy import deepcopy

from transmission_layers.expectation_failure import (
    build_path5b_fragility_propagation_report,
    build_path5c_propagation_persistence_evolution_report,
    build_path5d_propagation_regime_classification_report,
    build_path5d_propagation_regime_scores,
    build_path5d_regime_explainability,
    build_path5d_regime_inputs,
    build_path5d_regime_transition_summary,
    build_path5d_structural_state_labels,
    certify_path5d_propagation_regime_classification,
    classify_path5d_propagation_regime,
)


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


def _windows():
    b = build_path5b_fragility_propagation_report(_graph())
    return [
        {"window_index": 0, "window_id": "w0", **b},
        {"window_index": 1, "window_id": "w1", **b},
    ]


def test_api_presence_and_non_regression_exports():
    assert callable(build_path5d_regime_inputs)
    assert callable(build_path5d_propagation_regime_scores)
    assert callable(classify_path5d_propagation_regime)
    assert callable(build_path5d_structural_state_labels)
    assert callable(build_path5d_regime_transition_summary)
    assert callable(build_path5d_regime_explainability)
    assert callable(certify_path5d_propagation_regime_classification)
    assert callable(build_path5d_propagation_regime_classification_report)
    assert callable(build_path5b_fragility_propagation_report)
    assert callable(build_path5c_propagation_persistence_evolution_report)


def test_determinism_checksum_and_immutable_inputs_and_bounded_scores():
    b = build_path5b_fragility_propagation_report(_graph())
    c = build_path5c_propagation_persistence_evolution_report(_windows())
    b0, c0 = deepcopy(b), deepcopy(c)
    r1 = build_path5d_propagation_regime_classification_report(b, c)
    r2 = build_path5d_propagation_regime_classification_report(b, c)
    assert r1 == r2
    assert r1["report_checksum"] == r2["report_checksum"]
    assert b == b0 and c == c0
    for v in r1["regime_scores"].values():
        assert 0 <= float(v) <= 100


def test_missing_partial_inputs_and_insufficient_evidence():
    r = build_path5d_propagation_regime_classification_report({}, {})
    assert r["classification"]["selected_regime"] == "INSUFFICIENT_PROPAGATION_EVIDENCE"


def test_regime_classification_precedence_and_tiebreakers():
    s = {"evidence_sufficiency_score": 100, "carrier_dominance_score": 80, "corridor_weakness_score": 90, "amplification_regime_score": 90,
         "concentration_regime_score": 90, "breadth_regime_score": 90, "rotation_regime_score": 90, "stabilization_regime_score": 90,
         "persistence_regime_score": 90, "mixed_state_score": 90}
    c = classify_path5d_propagation_regime(s)
    assert c["selected_regime"] == "CARRIER_DOMINATED_PROPAGATION"
    assert classify_path5d_propagation_regime(s) == c


def test_each_required_regime_classifiable():
    base = {"evidence_sufficiency_score": 100, "carrier_dominance_score": 0, "corridor_weakness_score": 0, "amplification_regime_score": 0,
            "concentration_regime_score": 0, "breadth_regime_score": 0, "rotation_regime_score": 0, "stabilization_regime_score": 0,
            "persistence_regime_score": 0, "mixed_state_score": 0}
    cases = {
        "INSUFFICIENT_PROPAGATION_EVIDENCE": {"evidence_sufficiency_score": 0},
        "CARRIER_DOMINATED_PROPAGATION": {"carrier_dominance_score": 71},
        "CORRIDOR_WEAKENED_PROPAGATION": {"corridor_weakness_score": 71},
        "AMPLIFYING_PRESSURE_STRUCTURE": {"amplification_regime_score": 66},
        "CONCENTRATED_PRESSURE": {"concentration_regime_score": 66},
        "BROAD_DISTRIBUTED_FRAGILITY": {"breadth_regime_score": 66},
        "ROTATING_PROPAGATION": {"rotation_regime_score": 56},
        "STABILIZING_PROPAGATION": {"stabilization_regime_score": 71, "persistence_regime_score": 66},
        "ISOLATED_FRAGILITY": {"breadth_regime_score": 30, "concentration_regime_score": 30},
        "MIXED_PROPAGATION_STATE": {"mixed_state_score": 70, "breadth_regime_score": 40},
    }
    for regime, patch in cases.items():
        s = dict(base)
        s.update(patch)
        assert classify_path5d_propagation_regime(s)["selected_regime"] == regime


def test_transition_labels_structural_labels_explainability_and_certification_states():
    cur = {"selected_regime": "ROTATING_PROPAGATION"}
    prev = {"selected_regime": "CONCENTRATED_PRESSURE"}
    cs = {"rotation_regime_score": 70, "breadth_regime_score": 60, "concentration_regime_score": 60, "stabilization_regime_score": 40}
    ps = {"rotation_regime_score": 40, "breadth_regime_score": 40, "concentration_regime_score": 50, "stabilization_regime_score": 20}
    t = build_path5d_regime_transition_summary(cur, prev, cs, ps)
    assert t["transition_state"] in {"rotated regime", "broadened regime", "intensified regime", "stabilized regime", "unchanged regime", "narrowed regime"}
    labels = build_path5d_structural_state_labels(cur, {"concentration_regime_score": 80, "carrier_dominance_score": 80, "corridor_weakness_score": 80, "amplification_regime_score": 80, "rotation_regime_score": 80, "stabilization_regime_score": 80})
    assert "supervisor_state_label" in labels
    exp = build_path5d_regime_explainability(cur, {"concentration_regime_score": 80, "carrier_dominance_score": 80, "corridor_weakness_score": 80, "breadth_regime_score": 80, "rotation_regime_score": 80}, labels, t)
    assert exp["forbidden_term_violations"] == []
    r = build_path5d_propagation_regime_classification_report({}, {})
    assert r["certification"]["status"] in {
        "BLOCKED_PATH5D_PROPAGATION_REGIME_CLASSIFICATION",
        "DEGRADED_PATH5D_PROPAGATION_REGIME_CLASSIFICATION",
        "CERTIFIED_PATH5D_PROPAGATION_REGIME_CLASSIFICATION",
    }
