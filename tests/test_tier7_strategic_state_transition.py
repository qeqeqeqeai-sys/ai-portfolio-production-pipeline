from copy import deepcopy

from transmission_layers.intelligence.tier7 import assess_strategic_state_transition, classify_strategic_graph_state


def _state(label: str):
    return {"strategic_graph_state": label}


def test_deterministic_repeated_output_and_checksum_stability():
    first = assess_strategic_state_transition(_state("stable"), _state("stressed"))
    second = assess_strategic_state_transition(_state("stable"), _state("stressed"))
    assert first == second
    assert first["strategic_state_transition_checksum"] == second["strategic_state_transition_checksum"]


def test_each_transition_class_reachable():
    assert assess_strategic_state_transition(_state("stable"), _state("stable"))["transition_class"] == "unchanged"
    assert assess_strategic_state_transition(_state("stressed"), _state("stable"))["transition_class"] == "improved"
    assert assess_strategic_state_transition(_state("stable"), _state("transitional"))["transition_class"] == "deteriorated"
    assert assess_strategic_state_transition(_state("stable"), _state("distorted"))["transition_class"] == "destabilized"
    assert assess_strategic_state_transition(_state("structurally_blocked"), _state("stressed"))["transition_class"] == "recovering"
    assert assess_strategic_state_transition(_state("stable"), _state("structurally_blocked"))["transition_class"] == "blocked"
    assert assess_strategic_state_transition(_state("invalid_input"), _state("stable"))["transition_class"] == "invalid_transition"


def test_invalid_malformed_states_invalid_transition():
    assert assess_strategic_state_transition(None, _state("stable"))["transition_class"] == "invalid_transition"
    assert assess_strategic_state_transition(_state("stable"), {"strategic_graph_state": "unknown"})["transition_class"] == "invalid_transition"


def test_blocked_and_recovering_precedence():
    assert assess_strategic_state_transition(_state("structurally_blocked"), _state("structurally_blocked"))["transition_class"] == "blocked"
    assert assess_strategic_state_transition(_state("structurally_blocked"), _state("stable"))["transition_class"] == "recovering"


def test_unchanged_improved_deteriorated_destabilized_handling():
    assert assess_strategic_state_transition(_state("fragile"), _state("fragile"))["transition_class"] == "unchanged"
    assert assess_strategic_state_transition(_state("degraded"), _state("stressed"))["transition_class"] == "improved"
    assert assess_strategic_state_transition(_state("stable"), _state("stressed"))["transition_class"] == "deteriorated"
    assert assess_strategic_state_transition(_state("stressed"), _state("fragmented"))["transition_class"] == "destabilized"


def test_fixed_template_explanation_and_invariants():
    result = assess_strategic_state_transition(_state("stable"), _state("stressed"))
    assert result["explanation"].startswith("Strategic state transition intelligence is deterministic:")
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
    prev = _state("stable")
    curr = _state("stressed")
    prev_snapshot = deepcopy(prev)
    curr_snapshot = deepcopy(curr)
    assess_strategic_state_transition(prev, curr)
    assert prev == prev_snapshot
    assert curr == curr_snapshot


def test_public_api_export():
    from transmission_layers.intelligence import tier7

    assert hasattr(tier7, "assess_strategic_state_transition")


def test_tier7a_non_regression_smoke_check():
    evidence = {
        "nodes": [{"node_id": "A"}, {"node_id": "B"}],
        "edges": [{"source_node_id": "A", "target_node_id": "B", "edge_quality_score": 1.0}],
        "graph_health_score": 0.9,
    }
    result = classify_strategic_graph_state(evidence)
    assert result["strategic_graph_state"] == "stable"


def test_tier4_5_6_operational_non_regression_smoke_checks():
    from transmission_layers.intelligence.tier4.structural_entropy import compute_structural_entropy
    from transmission_layers.intelligence.tier5.federation_determinism import stable_checksum
    from transmission_layers.intelligence.tier6.transmission_explainability import assess_transmission_explainability
    from transmission_layers.operationalization.audit_summary import build_operational_audit_summary
    from pathlib import Path

    assert "entropy_score" in compute_structural_entropy([{"node_id": "A", "stress": 0.1}])
    assert stable_checksum({"x": 1}, prefix="smoke").startswith("smoke_")
    assert "explanation" in assess_transmission_explainability({"status": "ok"})
    summary = build_operational_audit_summary({}, Path("/tmp/tier7b-smoke"), overwrite=False)
    assert "audit_summary" in summary
