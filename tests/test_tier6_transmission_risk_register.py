from copy import deepcopy

from transmission_layers.intelligence.tier4.structural_simulation import run_structural_simulation
from transmission_layers.intelligence.tier6 import (
    assess_propagation_distortion_diagnostics,
    assess_structural_signal_quality,
    assess_transmission_explainability,
    assess_transmission_path_integrity,
    assess_transmission_reliability_diagnostics,
    assess_transmission_risk_register,
)

ALLOWED_RISK_LABELS = {
    "insufficient_structure", "elevated_structural_risk", "elevated_propagation_risk", "elevated_bottleneck_risk",
    "elevated_contamination_risk", "elevated_explainability_risk", "weak_remediation_readiness",
    "weak_containment_feasibility", "structurally_stable",
}
ALLOWED_RISK_TYPES = {
    "structural_weakness", "propagation_instability", "bottleneck_dependency", "contamination_risk", "contradictory_evidence",
    "weak_traceability", "fragmentation_risk", "explainability_gap", "isolated_structure",
}
ALLOWED_RISK_DIAG = {"critical_risk", "elevated_risk", "moderate_risk", "low_risk", "informational_risk"}
ALLOWED_REMEDIATION_TARGETS = {
    "improve_connectivity", "reduce_bottleneck_dependency", "stabilize_propagation", "reduce_contamination",
    "improve_traceability", "improve_structural_alignment", "improve_evidence_consistency", "improve_metadata_completeness",
}
ALLOWED_REMEDIATION_DIAG = {"immediate_priority", "high_priority", "moderate_priority", "low_priority"}
ALLOWED_CONTAINMENT_TARGETS = {
    "isolate_contaminated_paths", "isolate_unstable_nodes", "reduce_dependency_exposure", "contain_fragmented_propagation",
    "contain_contradictory_edges", "improve_structural_segmentation",
}
ALLOWED_CONTAINMENT_DIAG = {
    "strong_containment_candidate", "moderate_containment_candidate", "weak_containment_candidate", "containment_not_required",
}


def _sample_topology():
    return {
        "nodes": [{"node_id": "a", "influence_score": 0.8}, {"node_id": "b", "influence_score": 0.7}, {"node_id": "c", "influence_score": 0.6}],
        "edges": [
            {"source_node_id": "a", "target_node_id": "b", "edge_quality_score": 0.7},
            {"source_node_id": "b", "target_node_id": "c", "edge_quality_score": 0.75},
        ],
    }


def test_deterministic_output_checksum_and_bounded_scores():
    one = assess_transmission_risk_register(_sample_topology())
    two = assess_transmission_risk_register(_sample_topology())
    assert one == two
    assert one["checksum"] == two["checksum"]
    assert 0.0 <= one["risk_register_score"] <= 1.0
    for v in one["risk_components"].values():
        assert 0.0 <= v <= 1.0


def test_empty_missing_disconnected_and_explanation_template():
    assert assess_transmission_risk_register({})["status"] == "insufficient_structure"
    assert assess_transmission_risk_register({"edges": []})["status"] == "insufficient_structure"
    assert assess_transmission_risk_register({"nodes": [{"node_id": "a"}]})["status"] == "insufficient_structure"
    disconnected = assess_transmission_risk_register({"nodes": [{"node_id": "a"}, {"node_id": "b"}], "edges": []})
    assert "insufficient_structure" in disconnected["risk_labels"]
    assert disconnected["explanation"].startswith("Transmission risk register completed: status=")


def test_elevated_and_weak_risk_label_detection():
    base = {
        "nodes": [
            {"node_id": "a", "influence_score": 0.1, "role": "source"},
            {"node_id": "b", "influence_score": 0.1, "role": "sink"},
            {"node_id": "c", "influence_score": 0.1, "role": "sink"},
        ],
        "edges": [
            {"source_node_id": "a", "target_node_id": "b", "edge_quality_score": 0.1, "suppressed_for_propagation": True, "role": "relay", "contradictory": True},
            {"source_node_id": "a", "target_node_id": "c", "edge_quality_score": 0.1, "suppressed_for_propagation": True, "role": "relay"},
        ],
    }
    labels = set(assess_transmission_risk_register(base)["risk_labels"])
    assert "elevated_structural_risk" in labels
    assert "elevated_propagation_risk" in labels
    assert "elevated_bottleneck_risk" in labels
    assert "elevated_contamination_risk" in labels
    assert "elevated_explainability_risk" in labels

    weak_ready = {"nodes": [{"node_id": "a", "influence_score": 0.1, "role": "source"}, {"node_id": "b", "influence_score": 0.1, "role": "sink"}], "edges": [{"source_node_id": "a", "target_node_id": "b", "edge_quality_score": 0.0, "suppressed_for_propagation": True, "role": "relay", "contradictory": True}]}
    weak_labels = set(assess_transmission_risk_register(weak_ready)["risk_labels"])
    assert "weak_remediation_readiness" in weak_labels
    assert "weak_containment_feasibility" in weak_labels


def test_deterministic_ordering_and_controlled_vocabularies():
    out = assess_transmission_risk_register(_sample_topology())
    assert out["risk_inventory"] == sorted(out["risk_inventory"], key=lambda x: x["risk_id"])
    assert out["remediation_priorities"] == sorted(out["remediation_priorities"], key=lambda x: x["remediation_id"])
    assert out["containment_opportunities"] == sorted(out["containment_opportunities"], key=lambda x: x["containment_id"])
    assert set(out["risk_labels"]).issubset(ALLOWED_RISK_LABELS)
    for item in out["risk_inventory"]:
        assert item["risk_type"] in ALLOWED_RISK_TYPES
        assert item["diagnostic_label"] in ALLOWED_RISK_DIAG
    for item in out["remediation_priorities"]:
        assert item["target_issue"] in ALLOWED_REMEDIATION_TARGETS
        assert item["diagnostic_label"] in ALLOWED_REMEDIATION_DIAG
    for item in out["containment_opportunities"]:
        assert item["containment_target"] in ALLOWED_CONTAINMENT_TARGETS
        assert item["diagnostic_label"] in ALLOWED_CONTAINMENT_DIAG


def test_input_immutability_public_export_and_non_regressions():
    topology = _sample_topology()
    original = deepcopy(topology)
    _ = assess_transmission_risk_register(topology)
    assert topology == original
    from transmission_layers.intelligence.tier6 import assess_transmission_risk_register as exported
    assert exported is assess_transmission_risk_register

    assert "signal_quality_score" in assess_structural_signal_quality(topology)
    assert "transmission_reliability_score" in assess_transmission_reliability_diagnostics(topology)
    assert "path_integrity_score" in assess_transmission_path_integrity(topology)
    assert "propagation_integrity_score" in assess_propagation_distortion_diagnostics(topology)
    assert "explainability_score" in assess_transmission_explainability(topology)
    assert "simulation_health_state" in run_structural_simulation(topology)
