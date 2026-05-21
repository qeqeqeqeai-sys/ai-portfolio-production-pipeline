from copy import deepcopy

from transmission_layers.intelligence.tier4.structural_simulation import run_structural_simulation
from transmission_layers.intelligence.tier6 import assess_transmission_reliability_diagnostics
from transmission_layers.intelligence.tier6.structural_signal_quality import assess_structural_signal_quality


def _sample_topology():
    return {
        "nodes": [
            {"node_id": "B", "influence_score": 0.20, "contagion_score": 0.90, "resilience_score": 0.10},
            {"node_id": "A", "influence_score": 0.90, "contagion_score": 0.20, "resilience_score": 0.80},
        ],
        "edges": [
            {"source_node_id": "B", "target_node_id": "A", "edge_quality_score": 0.30, "suppressed_for_propagation": True},
            {"source_node_id": "A", "target_node_id": "B", "edge_quality_score": 0.90, "suppressed_for_propagation": False},
        ],
    }


def test_deterministic_repeated_output_and_checksum_stability():
    topology = _sample_topology()
    a = assess_transmission_reliability_diagnostics(topology)
    b = assess_transmission_reliability_diagnostics(topology)
    assert a == b
    assert a["checksum"] == b["checksum"]


def test_bounded_scores():
    result = assess_transmission_reliability_diagnostics(_sample_topology())
    assert 0.0 <= result["transmission_reliability_score"] <= 1.0
    for score in result["reliability_components"].values():
        assert 0.0 <= score <= 1.0


def test_empty_topology_handling():
    result = assess_transmission_reliability_diagnostics({})
    assert result["status"] == "insufficient_structure"
    assert result["diagnostics"]["empty_topology"] is True


def test_disconnected_topology_handling():
    result = assess_transmission_reliability_diagnostics({"nodes": [{"node_id": "A"}], "edges": []})
    assert result["diagnostics"]["disconnected_topology"] is True
    assert "disconnected_topology" in result["transmission_failure_modes"]


def test_weak_edge_reliability_detection():
    result = assess_transmission_reliability_diagnostics(_sample_topology())
    assert "weak_edge_reliability" in result["transmission_failure_modes"]


def test_unstable_node_influence_detection():
    result = assess_transmission_reliability_diagnostics(_sample_topology())
    assert "unstable_node_influence" in result["transmission_failure_modes"]


def test_noisy_propagation_detection():
    topology = _sample_topology()
    topology["edges"] = [{"source_node_id": "A", "target_node_id": "B", "edge_quality_score": 0.0, "suppressed_for_propagation": True}]
    result = assess_transmission_reliability_diagnostics(topology)
    assert "noisy_propagation" in result["transmission_failure_modes"]


def test_weak_causal_traceability_detection():
    result = assess_transmission_reliability_diagnostics({"nodes": [{"node_id": "A"}, {"node_id": "B"}], "edges": []})
    assert "weak_causal_traceability" in result["transmission_failure_modes"]


def test_deterministic_edge_diagnostic_ordering():
    result = assess_transmission_reliability_diagnostics(_sample_topology())
    assert [(e["source_node_id"], e["target_node_id"]) for e in result["edge_diagnostics"]] == [("A", "B"), ("B", "A")]


def test_deterministic_node_diagnostic_ordering():
    result = assess_transmission_reliability_diagnostics(_sample_topology())
    assert [n["node_id"] for n in result["node_diagnostics"]] == ["A", "B"]


def test_fixed_controlled_label_vocabularies():
    result = assess_transmission_reliability_diagnostics(_sample_topology())
    assert result["status"] in {"ok", "review", "insufficient_structure"}
    assert set(result["causal_diagnostic_labels"]).issubset({
        "causal_path_traceable", "causal_path_partially_traceable", "causal_path_weak_traceability"
    })
    assert {e["edge_diagnostic_label"] for e in result["edge_diagnostics"]}.issubset({"edge_reliable", "edge_moderate", "edge_weak"})
    assert {n["node_diagnostic_label"] for n in result["node_diagnostics"]}.issubset({"node_stable", "node_moderate", "node_unstable"})
    assert set(result["transmission_failure_modes"]).issubset({
        "none", "disconnected_topology", "weak_edge_reliability", "unstable_node_influence", "noisy_propagation", "weak_causal_traceability"
    })


def test_fixed_template_explanation():
    result = assess_transmission_reliability_diagnostics(_sample_topology())
    assert result["explanation"] == (
        "Tier 6B deterministic transmission reliability decomposition executed with bounded component scoring, "
        "sorted diagnostics ordering, controlled label vocabularies, and additive-only causal failure-mode tracing."
    )


def test_input_immutability():
    topology = _sample_topology()
    before = deepcopy(topology)
    _ = assess_transmission_reliability_diagnostics(topology)
    assert topology == before


def test_public_api_export():
    result = assess_transmission_reliability_diagnostics(_sample_topology())
    assert "checksum" in result


def test_tier6a_non_regression():
    result = assess_structural_signal_quality(_sample_topology())
    assert result["assessment_status"] == "success"


def test_tier4_smoke_non_regression():
    result = run_structural_simulation()
    assert result["simulation_run_id"] == "tier4a_deterministic_run"
