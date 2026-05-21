from copy import deepcopy

from transmission_layers.intelligence.tier4.structural_simulation import run_structural_simulation
from transmission_layers.intelligence.tier6 import (
    assess_propagation_distortion_diagnostics,
    assess_structural_signal_quality,
    assess_transmission_explainability,
    assess_transmission_governance_audit_trail,
    assess_transmission_governance_review_gate,
    assess_transmission_governance_summary,
    assess_transmission_path_integrity,
    assess_transmission_reliability_diagnostics,
    assess_transmission_risk_register,
)

ALLOWED_AUDIT_LABELS = {
    "insufficient_structure", "incomplete_audit_lineage", "weak_replay_evidence", "weak_dependency_reconstruction",
    "weak_review_consistency", "governance_reproducibility_risk", "deterministic_audit_gap", "governance_audit_complete",
}
ALLOWED_LINEAGE_TYPES = {
    "governance_review", "certification_decision", "remediation_review", "contamination_review",
    "explainability_review", "release_review", "structural_review",
}
ALLOWED_LINEAGE_DIAG = {"strong_lineage", "moderate_lineage", "weak_lineage", "missing_lineage"}
ALLOWED_TRACE_DIAG = {"traceable", "partially_traceable", "weakly_traceable", "non_traceable"}
ALLOWED_DEP_TYPES = {
    "structural_dependency", "propagation_dependency", "bottleneck_dependency", "contamination_dependency",
    "explainability_dependency", "remediation_dependency", "governance_dependency",
}
ALLOWED_DEP_DIAG = {"strongly_reconstructed", "moderately_reconstructed", "weakly_reconstructed", "reconstruction_gap"}
ALLOWED_REPLAY_TYPES = {
    "deterministic_review_evidence", "certification_evidence", "remediation_evidence", "contamination_evidence",
    "explainability_evidence", "governance_summary_evidence", "release_evidence",
}
ALLOWED_REPLAY_DIAG = {"replay_ready", "partially_replay_ready", "weak_replay_evidence", "replay_gap"}
ALLOWED_AUDIT_STATES = {"complete", "reviewable", "fragmented", "inconsistent", "insufficient_structure"}


def _sample_topology():
    return {
        "nodes": [{"node_id": "a", "influence_score": 0.8}, {"node_id": "b", "influence_score": 0.7}, {"node_id": "c", "influence_score": 0.6}],
        "edges": [
            {"source_node_id": "a", "target_node_id": "b", "edge_quality_score": 0.7},
            {"source_node_id": "b", "target_node_id": "c", "edge_quality_score": 0.75},
        ],
    }


def test_deterministic_repeated_output_checksum_stability_and_bounded_scores():
    one = assess_transmission_governance_audit_trail(_sample_topology())
    two = assess_transmission_governance_audit_trail(_sample_topology())
    assert one == two
    assert one["checksum"] == two["checksum"]
    assert 0.0 <= one["audit_integrity_score"] <= 1.0
    for value in one["audit_components"].values():
        assert 0.0 <= value <= 1.0


def test_empty_missing_and_disconnected_topology_handling():
    assert assess_transmission_governance_audit_trail({})["status"] == "insufficient_structure"
    assert assess_transmission_governance_audit_trail({"edges": []})["status"] == "insufficient_structure"
    assert assess_transmission_governance_audit_trail({"nodes": [{"node_id": "a"}]})["status"] == "insufficient_structure"
    disconnected = assess_transmission_governance_audit_trail({"nodes": [{"node_id": "a"}, {"node_id": "b"}], "edges": []})
    assert disconnected["diagnostics"]["is_empty"] is True


def test_detection_of_incomplete_lineage_and_weakness_labels():
    weak = {
        "nodes": [{"node_id": "a", "influence_score": 0.1}, {"node_id": "b", "influence_score": 0.1}, {"node_id": "c", "influence_score": 0.1}],
        "edges": [
            {"source_node_id": "a", "target_node_id": "b", "edge_quality_score": 0.1, "suppressed_for_propagation": True, "contradictory": True},
            {"source_node_id": "a", "target_node_id": "c", "edge_quality_score": 0.1, "suppressed_for_propagation": True},
        ],
    }
    out = assess_transmission_governance_audit_trail(weak)
    labels = set(out["audit_labels"])
    assert "incomplete_audit_lineage" in labels
    assert "weak_replay_evidence" in labels
    assert "weak_dependency_reconstruction" in labels
    assert "weak_review_consistency" in labels
    assert "governance_reproducibility_risk" in labels
    assert "deterministic_audit_gap" in labels


def test_deterministic_ordering_vocabularies_and_template_explanation():
    out = assess_transmission_governance_audit_trail(_sample_topology())
    assert out["certification_lineage"] == sorted(out["certification_lineage"], key=lambda x: (-x["lineage_score"], x["lineage_id"]))
    assert out["review_traceability_chain"] == sorted(out["review_traceability_chain"], key=lambda x: (-x["traceability_score"], x["trace_id"]))
    assert out["dependency_reconstruction"] == sorted(out["dependency_reconstruction"], key=lambda x: (-x["dependency_score"], x["dependency_id"]))
    assert out["replay_evidence_inventory"] == sorted(out["replay_evidence_inventory"], key=lambda x: (-x["evidence_score"], x["evidence_id"]))

    assert set(out["audit_labels"]).issubset(ALLOWED_AUDIT_LABELS)
    for item in out["certification_lineage"]:
        assert item["lineage_type"] in ALLOWED_LINEAGE_TYPES
        assert item["diagnostic_label"] in ALLOWED_LINEAGE_DIAG
    for item in out["review_traceability_chain"]:
        assert item["diagnostic_label"] in ALLOWED_TRACE_DIAG
    for item in out["dependency_reconstruction"]:
        assert item["dependency_type"] in ALLOWED_DEP_TYPES
        assert item["diagnostic_label"] in ALLOWED_DEP_DIAG
    for item in out["replay_evidence_inventory"]:
        assert item["evidence_type"] in ALLOWED_REPLAY_TYPES
        assert item["diagnostic_label"] in ALLOWED_REPLAY_DIAG
    assert out["audit_summary"]["overall_audit_state"] in ALLOWED_AUDIT_STATES

    expected = (
        f"Transmission governance audit trail completed: status={out['status']}; audit_integrity={out['audit_integrity_score']}; "
        f"primary_label={out['audit_summary']['primary_audit_label']}; lineage={len(out['certification_lineage'])}; "
        f"replay_evidence={len(out['replay_evidence_inventory'])}; dependencies={len(out['dependency_reconstruction'])}."
    )
    assert out["explanation"] == expected


def test_input_immutability_public_export_and_non_regression_smoke():
    topology = _sample_topology()
    original = deepcopy(topology)
    _ = assess_transmission_governance_audit_trail(topology)
    assert topology == original

    from transmission_layers.intelligence.tier6 import assess_transmission_governance_audit_trail as exported
    assert exported is assess_transmission_governance_audit_trail

    assert "signal_quality_score" in assess_structural_signal_quality(topology)
    assert "transmission_reliability_score" in assess_transmission_reliability_diagnostics(topology)
    assert "path_integrity_score" in assess_transmission_path_integrity(topology)
    assert "propagation_integrity_score" in assess_propagation_distortion_diagnostics(topology)
    assert "explainability_score" in assess_transmission_explainability(topology)
    assert "risk_register_score" in assess_transmission_risk_register(topology)
    assert "governance_score" in assess_transmission_governance_summary(topology)
    assert "governance_certification_score" in assess_transmission_governance_review_gate(topology)
    assert "simulation_health_state" in run_structural_simulation(topology)
