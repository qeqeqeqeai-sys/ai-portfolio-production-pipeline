from copy import deepcopy

from transmission_layers.intelligence.tier4.structural_simulation import run_structural_simulation
from transmission_layers.intelligence.tier6 import (
    assess_propagation_distortion_diagnostics,
    assess_structural_signal_quality,
    assess_transmission_explainability,
    assess_transmission_path_integrity,
    assess_transmission_reliability_diagnostics,
)

ALLOWED_EXPLAIN_LABELS = {
    "insufficient_evidence",
    "weak_signal_evidence",
    "weak_reliability_evidence",
    "weak_path_evidence",
    "weak_distortion_evidence",
    "contradictory_structural_evidence",
    "incomplete_attribution",
    "structurally_explainable",
}
ALLOWED_SOURCE_TIERS = {"tier6a", "tier6b", "tier6c", "tier6d"}
ALLOWED_EVIDENCE_TYPES = {
    "signal_quality", "reliability_component", "path_integrity", "bottleneck_attribution",
    "distortion_detection", "contamination_detection", "failure_mode", "structural_status",
}
ALLOWED_PRIMARY_LABELS = {"strong_evidence", "moderate_evidence", "weak_evidence", "missing_evidence", "contradictory_evidence"}
ALLOWED_SUPPORT_LABELS = {"supports_primary", "weak_support", "missing_support", "inconsistent_support"}
ALLOWED_CONTRA_LABELS = {"contradiction_detected", "weak_contradiction", "no_contradiction"}
ALLOWED_CAUSES = {
    "insufficient_structure", "weak_signal_quality", "weak_reliability", "path_bottleneck", "distorted_propagation",
    "contaminated_transmission", "weak_traceability", "contradictory_evidence", "no_material_issue_detected",
}
ALLOWED_ATTR_LABELS = {"primary_cause", "contributing_cause", "weak_cause", "no_issue"}


def _sample_topology():
    return {
        "nodes": [
            {"node_id": "a", "influence_score": 0.8, "centrality_score": 0.7, "resilience_score": 0.7, "fragmentation_score": 0.2, "role": "source"},
            {"node_id": "b", "influence_score": 0.6, "centrality_score": 0.6, "resilience_score": 0.5, "fragmentation_score": 0.3, "role": "relay"},
        ],
        "edges": [{"edge_id": "e1", "source_node_id": "a", "target_node_id": "b", "edge_quality_score": 0.75, "suppressed_for_propagation": False, "role": "relay"}],
    }


def test_deterministic_output_and_checksum_stability():
    topo = _sample_topology()
    one = assess_transmission_explainability(topo)
    two = assess_transmission_explainability(topo)
    assert one == two
    assert one["checksum"] == two["checksum"]


def test_bounded_scores_and_explanation_template():
    out = assess_transmission_explainability(_sample_topology())
    assert 0.0 <= out["explainability_score"] <= 1.0
    for v in out["evidence_components"].values():
        assert 0.0 <= v <= 1.0
    assert out["explanation"].startswith("Transmission explainability completed: status=")
    assert "; explainability=" in out["explanation"]


def test_empty_missing_and_disconnected_handling():
    assert assess_transmission_explainability({})["status"] == "insufficient_structure"
    assert assess_transmission_explainability({"edges": []})["status"] == "insufficient_structure"
    assert assess_transmission_explainability({"nodes": [{"node_id": "a"}]})["status"] == "insufficient_structure"
    disconnected = {"nodes": [{"node_id": "a"}, {"node_id": "b"}], "edges": []}
    labels = assess_transmission_explainability(disconnected)["explainability_labels"]
    assert "weak_path_evidence" in labels


def test_weak_evidence_and_contradictions_and_incomplete_attribution():
    topology = {
        "nodes": [{"node_id": "a", "influence_score": 0.1}, {"node_id": "b", "influence_score": 0.1}],
        "edges": [{"source_node_id": "a", "target_node_id": "b", "edge_quality_score": 0.1, "suppressed_for_propagation": True, "contradictory": True}],
    }
    out = assess_transmission_explainability(topology)
    labels = set(out["explainability_labels"])
    assert "weak_signal_evidence" in labels
    assert "weak_reliability_evidence" in labels
    assert "contradictory_structural_evidence" in labels
    weak_distortion = assess_transmission_explainability({"nodes": [{"node_id": "a"}], "edges": []})
    assert "weak_distortion_evidence" in set(weak_distortion["explainability_labels"])
    assert "incomplete_attribution" in set(weak_distortion["explainability_labels"])


def test_deterministic_inventory_ordering_and_controlled_vocabularies():
    out = assess_transmission_explainability(_sample_topology())
    assert out["primary_evidence"] == sorted(out["primary_evidence"], key=lambda x: x["evidence_id"])
    assert out["supporting_evidence"] == sorted(out["supporting_evidence"], key=lambda x: x["evidence_id"])
    assert out["contradictory_evidence"] == sorted(out["contradictory_evidence"], key=lambda x: x["evidence_id"])
    assert out["structural_attribution"] == sorted(out["structural_attribution"], key=lambda x: x["attribution_id"])
    assert set(out["explainability_labels"]).issubset(ALLOWED_EXPLAIN_LABELS)

    for item in out["primary_evidence"]:
        assert item["source_tier"] in ALLOWED_SOURCE_TIERS
        assert item["evidence_type"] in ALLOWED_EVIDENCE_TYPES
        assert item["diagnostic_label"] in ALLOWED_PRIMARY_LABELS
    for item in out["supporting_evidence"]:
        assert item["source_tier"] in ALLOWED_SOURCE_TIERS
        assert item["diagnostic_label"] in ALLOWED_SUPPORT_LABELS
    for item in out["contradictory_evidence"]:
        assert item["source_tier"] in ALLOWED_SOURCE_TIERS
        assert item["diagnostic_label"] in ALLOWED_CONTRA_LABELS
    for item in out["structural_attribution"]:
        assert item["structural_cause"] in ALLOWED_CAUSES
        assert item["diagnostic_label"] in ALLOWED_ATTR_LABELS


def test_input_immutability_and_public_api_export_and_non_regressions():
    topology = _sample_topology()
    original = deepcopy(topology)
    _ = assess_transmission_explainability(topology)
    assert topology == original
    from transmission_layers.intelligence.tier6 import assess_transmission_explainability as exported
    assert exported is assess_transmission_explainability

    assert "signal_quality_score" in assess_structural_signal_quality(topology)
    assert "transmission_reliability_score" in assess_transmission_reliability_diagnostics(topology)
    assert "path_integrity_score" in assess_transmission_path_integrity(topology)
    assert "propagation_integrity_score" in assess_propagation_distortion_diagnostics(topology)
    assert "simulation_health_state" in run_structural_simulation(topology)
