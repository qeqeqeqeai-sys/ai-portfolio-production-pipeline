from copy import deepcopy

from transmission_layers.intelligence.tier4.structural_simulation import run_structural_simulation
from transmission_layers.intelligence.tier6 import (
    assess_propagation_distortion_diagnostics,
    assess_structural_signal_quality,
    assess_transmission_explainability,
    assess_transmission_governance_review_gate,
    assess_transmission_governance_summary,
    assess_transmission_path_integrity,
    assess_transmission_reliability_diagnostics,
    assess_transmission_risk_register,
)

ALLOWED_REVIEW_LABELS = {
    "insufficient_structure", "certification_attention_required", "structural_certification_failure",
    "explainability_certification_failure", "remediation_certification_failure", "contamination_certification_failure",
    "governance_release_blocked", "operational_instability_detected", "governance_certified", "governance_release_ready",
}
ALLOWED_FINDING_TYPES = {
    "structural_gap", "propagation_gap", "bottleneck_gap", "contamination_gap", "explainability_gap",
    "remediation_gap", "deterministic_integrity_gap", "governance_release_gap",
}
ALLOWED_FINDING_DIAG = {"blocking_finding", "elevated_finding", "moderate_finding", "informational_finding"}
ALLOWED_FAILURE_TYPES = {
    "structural_failure", "explainability_failure", "remediation_failure", "contamination_failure",
    "deterministic_integrity_failure", "operational_readiness_failure", "governance_release_failure",
}
ALLOWED_FAILURE_DIAG = {"critical_failure", "elevated_failure", "moderate_failure", "no_failure"}
ALLOWED_REQ_TYPES = {
    "improve_connectivity", "improve_traceability", "reduce_contamination", "reduce_bottleneck_dependency",
    "improve_explainability", "improve_remediation_coverage", "improve_structural_consistency", "improve_deterministic_integrity",
}
ALLOWED_REQ_DIAG = {"mandatory_requirement", "high_requirement", "moderate_requirement", "optional_requirement"}
ALLOWED_DETERMINISM_STATES = {"deterministic", "partially_deterministic", "structurally_inconsistent", "insufficient_structure"}
ALLOWED_RELEASE_STATES = {"certified", "review_required", "blocked", "insufficient_structure"}


def _sample_topology():
    return {
        "nodes": [{"node_id": "a", "influence_score": 0.8}, {"node_id": "b", "influence_score": 0.7}, {"node_id": "c", "influence_score": 0.6}],
        "edges": [
            {"source_node_id": "a", "target_node_id": "b", "edge_quality_score": 0.7},
            {"source_node_id": "b", "target_node_id": "c", "edge_quality_score": 0.75},
        ],
    }


def test_deterministic_repeated_output_checksum_and_bounded_scores():
    one = assess_transmission_governance_review_gate(_sample_topology())
    two = assess_transmission_governance_review_gate(_sample_topology())
    assert one == two
    assert one["checksum"] == two["checksum"]
    assert 0.0 <= one["governance_certification_score"] <= 1.0
    for v in one["review_components"].values():
        assert 0.0 <= v <= 1.0


def test_empty_missing_disconnected_and_release_readiness_detection():
    assert assess_transmission_governance_review_gate({})["status"] == "insufficient_structure"
    assert assess_transmission_governance_review_gate({"edges": []})["status"] == "insufficient_structure"
    assert assess_transmission_governance_review_gate({"nodes": [{"node_id": "a"}]})["status"] == "insufficient_structure"
    disconnected = assess_transmission_governance_review_gate({"nodes": [{"node_id": "a"}, {"node_id": "b"}], "edges": []})
    assert disconnected["release_readiness"]["is_release_ready"] is False
    assert disconnected["release_readiness"]["requires_governance_review"] is True


def test_failure_detection_contamination_explainability_remediation_release_and_operational():
    weak = {
        "nodes": [{"node_id": "a", "influence_score": 0.1}, {"node_id": "b", "influence_score": 0.1}, {"node_id": "c", "influence_score": 0.1}],
        "edges": [
            {"source_node_id": "a", "target_node_id": "b", "edge_quality_score": 0.1, "suppressed_for_propagation": True, "contradictory": True},
            {"source_node_id": "a", "target_node_id": "c", "edge_quality_score": 0.1, "suppressed_for_propagation": True},
        ],
    }
    out = assess_transmission_governance_review_gate(weak)
    labels = set(out["review_labels"])
    assert "contamination_certification_failure" in labels
    assert "explainability_certification_failure" in labels
    assert "remediation_certification_failure" in labels
    assert "governance_release_blocked" in labels
    assert any(x["failure_type"] == "operational_readiness_failure" and x["failure_score"] > 0.0 for x in out["certification_failures"])
    assert out["certification_summary"]["deterministic_integrity_state"] in {"partially_deterministic", "structurally_inconsistent", "insufficient_structure"}


def test_deterministic_ordering_and_controlled_vocabularies_and_template_explanation():
    out = assess_transmission_governance_review_gate(_sample_topology())
    assert out["review_findings"] == sorted(out["review_findings"], key=lambda x: (-x["severity_score"], x["finding_id"]))
    assert out["certification_failures"] == sorted(out["certification_failures"], key=lambda x: (-x["failure_score"], x["failure_id"]))
    assert out["remediation_requirements"] == sorted(out["remediation_requirements"], key=lambda x: (-x["requirement_score"], x["requirement_id"]))
    assert set(out["review_labels"]).issubset(ALLOWED_REVIEW_LABELS)
    for x in out["review_findings"]:
        assert x["finding_type"] in ALLOWED_FINDING_TYPES
        assert x["diagnostic_label"] in ALLOWED_FINDING_DIAG
    for x in out["certification_failures"]:
        assert x["failure_type"] in ALLOWED_FAILURE_TYPES
        assert x["diagnostic_label"] in ALLOWED_FAILURE_DIAG
    for x in out["remediation_requirements"]:
        assert x["requirement_type"] in ALLOWED_REQ_TYPES
        assert x["diagnostic_label"] in ALLOWED_REQ_DIAG
    assert out["certification_summary"]["deterministic_integrity_state"] in ALLOWED_DETERMINISM_STATES
    assert out["certification_summary"]["overall_release_state"] in ALLOWED_RELEASE_STATES
    expected = (
        f"Transmission governance review gate completed: status={out['status']}; certification={out['governance_certification_score']}; "
        f"primary_label={out['certification_summary']['primary_review_label']}; findings={len(out['review_findings'])}; "
        f"failures={len(out['certification_failures'])}; requirements={len(out['remediation_requirements'])}."
    )
    assert out["explanation"] == expected


def test_input_immutability_public_export_and_non_regression_smoke():
    topology = _sample_topology()
    original = deepcopy(topology)
    _ = assess_transmission_governance_review_gate(topology)
    assert topology == original

    from transmission_layers.intelligence.tier6 import assess_transmission_governance_review_gate as exported
    assert exported is assess_transmission_governance_review_gate

    assert "signal_quality_score" in assess_structural_signal_quality(topology)
    assert "transmission_reliability_score" in assess_transmission_reliability_diagnostics(topology)
    assert "path_integrity_score" in assess_transmission_path_integrity(topology)
    assert "propagation_integrity_score" in assess_propagation_distortion_diagnostics(topology)
    assert "explainability_score" in assess_transmission_explainability(topology)
    assert "risk_register_score" in assess_transmission_risk_register(topology)
    assert "governance_score" in assess_transmission_governance_summary(topology)
    assert "simulation_health_state" in run_structural_simulation(topology)
