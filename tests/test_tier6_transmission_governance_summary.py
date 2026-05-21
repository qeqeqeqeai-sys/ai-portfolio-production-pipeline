from copy import deepcopy

from transmission_layers.intelligence.tier4.structural_simulation import run_structural_simulation
from transmission_layers.intelligence.tier6 import (
    assess_propagation_distortion_diagnostics,
    assess_structural_signal_quality,
    assess_transmission_explainability,
    assess_transmission_governance_summary,
    assess_transmission_path_integrity,
    assess_transmission_reliability_diagnostics,
    assess_transmission_risk_register,
)

ALLOWED_GOVERNANCE_LABELS = {
    "insufficient_structure", "governance_attention_required", "elevated_structural_governance_risk",
    "elevated_propagation_governance_risk", "elevated_contamination_governance_risk", "elevated_bottleneck_governance_risk",
    "weak_explainability_governance", "weak_remediation_governance", "governance_ready", "operationally_stable",
}
ALLOWED_OPERATIONAL_STATES = {"stable", "stressed", "fragmented", "contaminated", "bottlenecked", "insufficient_structure"}
ALLOWED_BOTTLENECK_TYPES = {"node_bottleneck", "edge_bottleneck", "path_bottleneck"}
ALLOWED_BOTTLENECK_DIAG = {"severe_bottleneck", "elevated_bottleneck", "moderate_bottleneck", "low_bottleneck"}
ALLOWED_CONTAMINATION_TYPES = {"distorted_edge", "contaminated_node", "fragmented_path", "contradictory_transmission", "weak_semantic_alignment"}
ALLOWED_CONTAMINATION_DIAG = {"severe_contamination", "elevated_contamination", "moderate_contamination", "low_contamination"}


def _sample_topology():
    return {
        "nodes": [{"node_id": "a", "influence_score": 0.8}, {"node_id": "b", "influence_score": 0.7}, {"node_id": "c", "influence_score": 0.6}],
        "edges": [
            {"source_node_id": "a", "target_node_id": "b", "edge_quality_score": 0.7},
            {"source_node_id": "b", "target_node_id": "c", "edge_quality_score": 0.75},
        ],
    }


def test_deterministic_checksum_bounded_scores_and_ordering():
    one = assess_transmission_governance_summary(_sample_topology())
    two = assess_transmission_governance_summary(_sample_topology())
    assert one == two
    assert one["checksum"] == two["checksum"]
    assert 0.0 <= one["governance_score"] <= 1.0
    for v in one["governance_components"].values():
        assert 0.0 <= v <= 1.0
    assert one["top_risks"] == sorted(one["top_risks"], key=lambda x: (-x["severity_score"], x["risk_id"]))
    assert one["top_evidence"] == sorted(one["top_evidence"], key=lambda x: (-x["evidence_score"], x["evidence_id"]))
    assert one["top_bottlenecks"] == sorted(one["top_bottlenecks"], key=lambda x: (-x["dependency_score"], x["bottleneck_id"]))
    assert one["top_contamination_findings"] == sorted(one["top_contamination_findings"], key=lambda x: (-x["contamination_score"], x["finding_id"]))
    assert one["top_remediation_priorities"] == sorted(one["top_remediation_priorities"], key=lambda x: (-x["priority_score"], x["remediation_id"]))


def test_empty_missing_disconnected_and_fixed_template_explanation():
    assert assess_transmission_governance_summary({})["status"] == "insufficient_structure"
    assert assess_transmission_governance_summary({"edges": []})["status"] == "insufficient_structure"
    assert assess_transmission_governance_summary({"nodes": [{"node_id": "a"}]})["status"] == "insufficient_structure"
    disconnected = assess_transmission_governance_summary({"nodes": [{"node_id": "a"}, {"node_id": "b"}], "edges": []})
    assert disconnected["executive_summary"]["overall_operational_state"] == "insufficient_structure"
    assert disconnected["explanation"].startswith("Transmission governance summary completed: status=")


def test_elevated_weak_labels_readiness_and_operational_detection():
    weak = {
        "nodes": [{"node_id": "a", "influence_score": 0.1}, {"node_id": "b", "influence_score": 0.1}, {"node_id": "c", "influence_score": 0.1}],
        "edges": [
            {"source_node_id": "a", "target_node_id": "b", "edge_quality_score": 0.1, "suppressed_for_propagation": True, "contradictory": True},
            {"source_node_id": "a", "target_node_id": "c", "edge_quality_score": 0.1, "suppressed_for_propagation": True},
        ],
    }
    out = assess_transmission_governance_summary(weak)
    labels = set(out["governance_labels"])
    assert "elevated_structural_governance_risk" in labels
    assert "weak_explainability_governance" in labels
    assert "weak_remediation_governance" in labels
    assert not out["governance_readiness"]["is_operationally_stable"]

    strong = _sample_topology()
    sout = assess_transmission_governance_summary(strong)
    assert sout["governance_readiness"]["is_governance_ready"]


def test_controlled_vocabularies_and_public_export_and_non_regression():
    out = assess_transmission_governance_summary(_sample_topology())
    assert set(out["governance_labels"]).issubset(ALLOWED_GOVERNANCE_LABELS)
    assert out["executive_summary"]["overall_operational_state"] in ALLOWED_OPERATIONAL_STATES
    for x in out["top_bottlenecks"]:
        assert x["bottleneck_type"] in ALLOWED_BOTTLENECK_TYPES
        assert x["diagnostic_label"] in ALLOWED_BOTTLENECK_DIAG
    for x in out["top_contamination_findings"]:
        assert x["finding_type"] in ALLOWED_CONTAMINATION_TYPES
        assert x["diagnostic_label"] in ALLOWED_CONTAMINATION_DIAG

    from transmission_layers.intelligence.tier6 import assess_transmission_governance_summary as exported
    assert exported is assess_transmission_governance_summary

    topology = _sample_topology()
    original = deepcopy(topology)
    _ = assess_transmission_governance_summary(topology)
    assert topology == original

    assert "signal_quality_score" in assess_structural_signal_quality(topology)
    assert "transmission_reliability_score" in assess_transmission_reliability_diagnostics(topology)
    assert "path_integrity_score" in assess_transmission_path_integrity(topology)
    assert "propagation_integrity_score" in assess_propagation_distortion_diagnostics(topology)
    assert "explainability_score" in assess_transmission_explainability(topology)
    assert "risk_register_score" in assess_transmission_risk_register(topology)
    assert "simulation_health_state" in run_structural_simulation(topology)
