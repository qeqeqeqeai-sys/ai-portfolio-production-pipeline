from copy import deepcopy

from transmission_layers.intelligence.tier4.structural_simulation import run_structural_simulation
from transmission_layers.intelligence.tier6 import (
    assess_structural_signal_quality,
    assess_transmission_path_integrity,
    assess_transmission_reliability_diagnostics,
)


def _sample_topology():
    return {
        "nodes": [{"node_id": "C"}, {"node_id": "A"}, {"node_id": "B"}],
        "edges": [
            {"edge_id": "e2", "source_node_id": "B", "target_node_id": "C", "edge_quality_score": 0.3, "suppressed_for_propagation": False},
            {"edge_id": "e1", "source_node_id": "A", "target_node_id": "B", "edge_quality_score": 0.9, "suppressed_for_propagation": False},
        ],
    }


def test_deterministic_repeated_output_and_checksum_stability():
    topology = _sample_topology()
    a = assess_transmission_path_integrity(topology)
    b = assess_transmission_path_integrity(topology)
    assert a == b
    assert a["checksum"] == b["checksum"]


def test_bounded_scores():
    result = assess_transmission_path_integrity(_sample_topology())
    assert 0.0 <= result["path_integrity_score"] <= 1.0
    for score in result["path_components"].values():
        assert 0.0 <= score <= 1.0


def test_empty_topology_handling():
    result = assess_transmission_path_integrity({})
    assert result["status"] == "insufficient_structure"
    assert "empty_topology" in result["path_integrity_labels"]


def test_missing_nodes_handling():
    result = assess_transmission_path_integrity({"nodes": [], "edges": [{"source_node_id": "A", "target_node_id": "B"}]})
    assert "missing_nodes" in result["path_failure_modes"]


def test_missing_edges_handling():
    result = assess_transmission_path_integrity({"nodes": [{"node_id": "A"}], "edges": []})
    assert "missing_edges" in result["path_failure_modes"]


def test_disconnected_topology_and_no_paths_detected_handling():
    result = assess_transmission_path_integrity({"nodes": [{"node_id": "A"}, {"node_id": "B"}], "edges": []})
    assert "disconnected_topology" in result["path_failure_modes"]
    assert "no_paths_detected" in result["path_failure_modes"]


def test_bottleneck_node_and_edge_detection():
    topology = {
        "nodes": [{"node_id": "A"}, {"node_id": "B"}, {"node_id": "C"}],
        "edges": [
            {"edge_id": "e1", "source_node_id": "A", "target_node_id": "B", "edge_quality_score": 0.7, "suppressed_for_propagation": False},
            {"edge_id": "e2", "source_node_id": "C", "target_node_id": "B", "edge_quality_score": 0.7, "suppressed_for_propagation": False},
        ],
    }
    result = assess_transmission_path_integrity(topology)
    assert any(n["diagnostic_label"] == "bottleneck_node" for n in result["bottleneck_nodes"])
    assert any(e["diagnostic_label"] == "bottleneck_edge" for e in result["bottleneck_edges"])


def test_weak_route_redundancy_inconsistent_edges_and_weak_trace_continuity_detection():
    topology = {"nodes": [{"node_id": "A"}, {"node_id": "B"}, {"node_id": "C"}], "edges": [{"source_node_id": "A", "target_node_id": "B"}]}
    result = assess_transmission_path_integrity(topology)
    assert "weak_route_redundancy" in result["path_integrity_labels"]
    assert "inconsistent_path_edges" in result["path_integrity_labels"]
    assert "weak_trace_continuity" in result["path_integrity_labels"]


def test_deterministic_orderings():
    result = assess_transmission_path_integrity(_sample_topology())
    assert [p["path_id"] for p in result["path_diagnostics"]] == sorted(p["path_id"] for p in result["path_diagnostics"])
    assert [n["node_id"] for n in result["bottleneck_nodes"]] == sorted(n["node_id"] for n in result["bottleneck_nodes"])
    edge_triplets = [(e["source"], e["target"], e["edge_id"]) for e in result["bottleneck_edges"]]
    assert edge_triplets == sorted(edge_triplets)


def test_controlled_label_vocab_and_fixed_template_explanation_and_input_immutability():
    topology = _sample_topology()
    before = deepcopy(topology)
    result = assess_transmission_path_integrity(topology)
    assert topology == before
    assert result["status"] in {"success", "insufficient_structure", "completed_with_findings"}
    assert set(result["path_integrity_labels"]).issubset({
        "empty_topology", "no_transmission_paths", "disconnected_paths", "bottleneck_dominated",
        "weak_route_redundancy", "inconsistent_path_edges", "weak_trace_continuity", "path_integrity_stable",
    })
    assert {p["diagnostic_label"] for p in result["path_diagnostics"]}.issubset({"stable_path", "weak_path", "broken_path", "bottleneck_path", "incomplete_path_metadata"})
    assert {n["diagnostic_label"] for n in result["bottleneck_nodes"]}.issubset({"bottleneck_node", "moderate_dependency_node", "low_dependency_node", "isolated_node"})
    assert {e["diagnostic_label"] for e in result["bottleneck_edges"]}.issubset({"bottleneck_edge", "moderate_dependency_edge", "low_dependency_edge", "incomplete_edge"})
    assert set(result["path_failure_modes"]).issubset({
        "empty_topology", "missing_nodes", "missing_edges", "disconnected_topology", "no_paths_detected",
        "single_route_dependency", "node_bottleneck_detected", "edge_bottleneck_detected", "incomplete_path_metadata",
        "weak_trace_continuity", "none_detected",
    })
    assert result["explanation"].startswith("Transmission path integrity completed: status=")


def test_public_api_export_and_non_regressions():
    result = assess_transmission_path_integrity(_sample_topology())
    assert "checksum" in result
    assert assess_structural_signal_quality(_sample_topology())["assessment_status"] == "success"
    assert assess_transmission_reliability_diagnostics(_sample_topology())["status"] in {"ok", "review", "insufficient_structure"}
    assert run_structural_simulation()["simulation_run_id"] == "tier4a_deterministic_run"
