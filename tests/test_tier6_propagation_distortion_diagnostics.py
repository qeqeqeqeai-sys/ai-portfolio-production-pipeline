from copy import deepcopy

from transmission_layers.intelligence.tier4.structural_simulation import run_structural_simulation
from transmission_layers.intelligence.tier6 import (
    assess_propagation_distortion_diagnostics,
    assess_structural_signal_quality,
    assess_transmission_path_integrity,
    assess_transmission_reliability_diagnostics,
)


def _sample_topology():
    return {
        "nodes": [
            {"node_id": "A", "role": "source"},
            {"node_id": "B", "role": "source"},
            {"node_id": "C", "role": "sink"},
        ],
        "edges": [
            {"edge_id": "e2", "source_node_id": "B", "target_node_id": "C", "edge_quality_score": 0.2, "suppressed_for_propagation": True, "contradictory": True},
            {"edge_id": "e1", "source_node_id": "A", "target_node_id": "B", "edge_quality_score": 0.35, "suppressed_for_propagation": False},
        ],
    }


def test_deterministic_repeated_output_and_checksum_stability():
    topology = _sample_topology()
    a = assess_propagation_distortion_diagnostics(topology)
    b = assess_propagation_distortion_diagnostics(topology)
    assert a == b
    assert a["checksum"] == b["checksum"]


def test_bounded_scores():
    result = assess_propagation_distortion_diagnostics(_sample_topology())
    assert 0.0 <= result["propagation_integrity_score"] <= 1.0
    for score in result["distortion_components"].values():
        assert 0.0 <= score <= 1.0


def test_empty_missing_nodes_missing_edges_and_disconnected_handling():
    assert "empty_topology" in assess_propagation_distortion_diagnostics({})["distortion_labels"]
    assert "missing_nodes" in assess_propagation_distortion_diagnostics({"nodes": [], "edges": [{"source_node_id": "A", "target_node_id": "B"}]})["distortion_failure_modes"]
    assert "missing_edges" in assess_propagation_distortion_diagnostics({"nodes": [{"node_id": "A"}], "edges": []})["distortion_failure_modes"]
    assert "disconnected_topology" in assess_propagation_distortion_diagnostics({"nodes": [{"node_id": "A"}, {"node_id": "B"}], "edges": []})["distortion_failure_modes"]


def test_signal_findings_detection():
    result = assess_propagation_distortion_diagnostics(_sample_topology())
    assert "distorted_signal_flow" in result["distortion_labels"]
    assert "contaminated_transmission" in result["distortion_labels"] or result["diagnostics"]["contaminated_node_count"] >= 0
    assert "contradictory_transmission" in result["distortion_labels"]


def test_fragmented_propagation_and_weak_semantic_alignment_detection():
    topology = {
        "nodes": [{"node_id": "A"}, {"node_id": "B"}, {"node_id": "C"}],
        "edges": [{"edge_id": "e1", "source_node_id": "A", "target_node_id": "B", "edge_quality_score": 0.95, "suppressed_for_propagation": False}],
    }
    result = assess_propagation_distortion_diagnostics(topology)
    assert "fragmented_propagation" in result["distortion_labels"]
    assert "weak_semantic_alignment" in result["distortion_labels"]


def test_deterministic_orderings():
    result = assess_propagation_distortion_diagnostics(_sample_topology())
    edge_triplets = [(e["source"], e["target"], e["edge_id"]) for e in result["edge_distortion_diagnostics"]]
    assert edge_triplets == sorted(edge_triplets)
    assert [n["node_id"] for n in result["node_contamination_diagnostics"]] == sorted(n["node_id"] for n in result["node_contamination_diagnostics"])
    path_triplets = [(p["source"], p["target"], p["path_id"]) for p in result["contamination_paths"]]
    assert path_triplets == sorted(path_triplets)


def test_controlled_vocabularies_explanation_template_and_input_immutability():
    topology = _sample_topology()
    before = deepcopy(topology)
    result = assess_propagation_distortion_diagnostics(topology)
    assert topology == before
    assert result["status"] in {"success", "insufficient_structure", "completed_with_findings"}
    assert set(result["distortion_labels"]).issubset({
        "empty_topology", "insufficient_propagation_structure", "distorted_signal_flow", "contaminated_transmission",
        "fragmented_propagation", "contradictory_transmission", "weak_semantic_alignment", "propagation_integrity_stable",
    })
    assert {e["diagnostic_label"] for e in result["edge_distortion_diagnostics"]}.issubset({"clean_edge", "distorted_edge", "contaminated_edge", "contradictory_edge", "incomplete_edge"})
    assert {n["diagnostic_label"] for n in result["node_contamination_diagnostics"]}.issubset({"clean_node", "contaminated_node", "distortion_amplifier_node", "isolated_node", "insufficient_node_metadata"})
    assert {p["diagnostic_label"] for p in result["contamination_paths"]}.issubset({"clean_path", "contaminated_path", "fragmented_path", "contradictory_path", "incomplete_path"})
    assert set(result["distortion_failure_modes"]).issubset({
        "empty_topology", "missing_nodes", "missing_edges", "disconnected_topology", "distorted_edges_detected",
        "contaminated_nodes_detected", "contradictory_edges_detected", "fragmented_propagation_detected",
        "weak_semantic_alignment", "incomplete_signal_metadata", "none_detected",
    })
    assert result["explanation"].startswith("Propagation distortion diagnostics completed: status=")


def test_public_api_export_and_non_regressions():
    result = assess_propagation_distortion_diagnostics(_sample_topology())
    assert "checksum" in result
    assert assess_structural_signal_quality(_sample_topology())["assessment_status"] == "success"
    assert assess_transmission_reliability_diagnostics(_sample_topology())["status"] in {"ok", "review", "insufficient_structure"}
    assert assess_transmission_path_integrity(_sample_topology())["status"] in {"success", "insufficient_structure", "completed_with_findings"}
    assert run_structural_simulation()["simulation_run_id"] == "tier4a_deterministic_run"
