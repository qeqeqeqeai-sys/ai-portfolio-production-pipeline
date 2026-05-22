from copy import deepcopy

from transmission_layers.intelligence.tier7 import classify_strategic_graph_state


def _base_evidence():
    return {
        "nodes": [{"node_id": "A"}, {"node_id": "B"}],
        "edges": [{"edge_id": "e1", "source_node_id": "A", "target_node_id": "B", "edge_quality_score": 1.0, "suppressed_for_propagation": False}],
        "graph_health_score": 0.95,
        "distortion_score": 0.1,
        "transition_pressure_score": 0.0,
        "regime_shift_signal": 0.0,
    }


def test_deterministic_repeated_output_and_checksum_stability():
    evidence = _base_evidence()
    first = classify_strategic_graph_state(evidence)
    second = classify_strategic_graph_state(evidence)
    assert first == second
    assert first["strategic_graph_state_checksum"] == second["strategic_graph_state_checksum"]


def test_each_strategic_state_reachable():
    stable = classify_strategic_graph_state(_base_evidence())
    stressed = classify_strategic_graph_state({**_base_evidence(), "graph_health_score": 0.8})
    fragile = classify_strategic_graph_state({**_base_evidence(), "graph_health_score": 0.4})
    distorted = classify_strategic_graph_state({**_base_evidence(), "distortion_score": 0.8})
    fragmented = classify_strategic_graph_state({**_base_evidence(), "edges": [{"edge_id": "x", "source_node_id": "A", "target_node_id": "X"}]})
    transitional = classify_strategic_graph_state({**_base_evidence(), "graph_health_score": 0.6})
    regime_shifting = classify_strategic_graph_state({**_base_evidence(), "regime_shift_signal": 0.9})
    degraded = classify_strategic_graph_state({**_base_evidence(), "graph_health_score": 0.2})
    blocked = classify_strategic_graph_state({**_base_evidence(), "edges": [{"source_node_id": "A", "target_node_id": "B", "suppressed_for_propagation": True}]})
    invalid = classify_strategic_graph_state({"nodes": "bad", "edges": []})

    assert stable["strategic_graph_state"] == "stable"
    assert stressed["strategic_graph_state"] == "stressed"
    assert fragile["strategic_graph_state"] == "fragile"
    assert distorted["strategic_graph_state"] == "distorted"
    assert fragmented["strategic_graph_state"] == "fragmented"
    assert transitional["strategic_graph_state"] == "transitional"
    assert regime_shifting["strategic_graph_state"] == "regime_shifting"
    assert degraded["strategic_graph_state"] == "degraded"
    assert blocked["strategic_graph_state"] == "structurally_blocked"
    assert invalid["strategic_graph_state"] == "invalid_input"


def test_precedence_ordering():
    evidence = {
        "nodes": [],
        "edges": [],
        "graph_health_score": 0.1,
        "regime_shift_signal": 0.9,
    }
    result = classify_strategic_graph_state(evidence)
    assert result["strategic_graph_state"] == "degraded"


def test_malformed_input_invalid_input():
    assert classify_strategic_graph_state(None)["strategic_graph_state"] == "invalid_input"


def test_empty_and_disconnected_graph_handling():
    empty = classify_strategic_graph_state({"nodes": [], "edges": []})
    disconnected = classify_strategic_graph_state({"nodes": [{"node_id": "A"}], "edges": [{"source_node_id": "A", "target_node_id": "B"}]})
    assert empty["evidence_summary"]["empty_graph"] is True
    assert empty["strategic_graph_state"] == "fragmented"
    assert disconnected["strategic_graph_state"] == "fragmented"


def test_fixed_template_explanation_and_invariants():
    result = classify_strategic_graph_state(_base_evidence())
    assert result["explanation"].startswith("Strategic graph-state classification is deterministic:")
    for flag in (
        "deterministic_output",
        "replay_compatible",
        "immutable_input_safe",
        "no_runtime_mutation",
        "no_adaptive_control",
        "no_prediction_engine",
        "additive_only",
    ):
        assert result["invariant_flags"][flag] is True


def test_immutable_input_safety_and_no_runtime_mutation_behavior():
    evidence = _base_evidence()
    snapshot = deepcopy(evidence)
    classify_strategic_graph_state(evidence)
    assert evidence == snapshot


def test_public_api_export():
    from transmission_layers.intelligence import tier7

    assert hasattr(tier7, "classify_strategic_graph_state")


def test_operational_non_regression_smoke():
    from transmission_layers.intelligence.tier4.structural_entropy import compute_structural_entropy
    from transmission_layers.intelligence.tier5.federation_determinism import stable_checksum
    from transmission_layers.intelligence.tier6.transmission_explainability import assess_transmission_explainability

    entropy = compute_structural_entropy([{"node_id": "A", "stress": 0.1}])
    chk = stable_checksum({"x": 1}, prefix="smoke")
    explain = assess_transmission_explainability({"status": "ok"})

    assert "entropy_score" in entropy
    assert chk.startswith("smoke_")
    assert "explanation" in explain
