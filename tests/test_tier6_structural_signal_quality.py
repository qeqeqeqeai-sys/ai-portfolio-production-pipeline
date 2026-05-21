from copy import deepcopy

from transmission_layers.intelligence.tier4.structural_simulation import run_structural_simulation
from transmission_layers.intelligence.tier6.structural_signal_quality import assess_structural_signal_quality


def _sample_topology():
    return {
        "nodes": [
            {"node_id": "B", "influence_score": 0.6, "contagion_score": 0.3, "centrality_score": 0.7, "resilience_score": 0.5, "fragmentation_score": 0.4},
            {"node_id": "A", "influence_score": 0.8, "contagion_score": 0.2, "centrality_score": 0.9, "resilience_score": 0.7, "fragmentation_score": 0.1},
        ],
        "edges": [
            {"source_node_id": "B", "target_node_id": "A", "edge_quality_score": 0.4, "suppressed_for_propagation": True},
            {"source_node_id": "A", "target_node_id": "B", "edge_quality_score": 0.9, "suppressed_for_propagation": False},
        ],
    }


def test_deterministic_repeated_output_and_checksum_stability():
    topology = _sample_topology()
    a = assess_structural_signal_quality(topology)
    b = assess_structural_signal_quality(topology)
    assert a == b
    assert a["checksum"] == b["checksum"]


def test_empty_topology_handling():
    result = assess_structural_signal_quality({})
    assert result["diagnostics"]["empty_topology"] is True
    assert result["confidence_label"] == "insufficient_structure"
    assert result["weak_link_count"] == 0


def test_disconnected_topology_handling():
    result = assess_structural_signal_quality({"nodes": [{"node_id": "A", "influence_score": 0.5}], "edges": []})
    assert result["diagnostics"]["disconnected_topology"] is True
    assert result["confidence_label"] == "insufficient_structure"


def test_weak_link_detection_and_ordering():
    result = assess_structural_signal_quality(_sample_topology())
    assert result["weak_link_count"] == 1
    assert result["weak_links"][0]["source_node_id"] == "B"
    assert [n["node_id"] for n in result["node_quality_inventory"]] == ["A", "B"]


def test_bounded_scores_and_confidence_label_set():
    result = assess_structural_signal_quality(_sample_topology())
    for key in [
        "signal_quality_score",
        "transmission_reliability_score",
        "node_influence_stability_score",
        "propagation_noise_score",
    ]:
        assert 0.0 <= result[key] <= 1.0
    assert result["confidence_label"] in {"strong", "moderate", "weak", "insufficient_structure"}


def test_input_immutable_safety():
    topology = _sample_topology()
    before = deepcopy(topology)
    _ = assess_structural_signal_quality(topology)
    assert topology == before


def test_fixed_template_explanation():
    result = assess_structural_signal_quality(_sample_topology())
    assert result["explanation"] == (
        "Tier 6A deterministic structural signal quality assessment executed with bounded scoring, "
        "sorted topology inventories, and weak-link diagnostics."
    )


def test_no_tier4_smoke_regression():
    result = run_structural_simulation()
    assert result["simulation_run_id"] == "tier4a_deterministic_run"
