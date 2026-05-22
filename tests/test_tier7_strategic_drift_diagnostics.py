from copy import deepcopy

from transmission_layers.intelligence.tier7 import (
    assess_strategic_state_transition,
    classify_strategic_graph_state,
    diagnose_strategic_drift,
)


def _s(label: str):
    return {"strategic_graph_state": label}


def _t(label: str):
    return {"transition_class": label}


def test_deterministic_repeated_output_and_checksum_stability():
    states = [_s("stable"), _s("stressed"), _s("transitional")]
    transitions = [_t("deteriorated"), _t("deteriorated")]
    first = diagnose_strategic_drift(states, transitions)
    second = diagnose_strategic_drift(states, transitions)
    assert first == second
    assert first["strategic_drift_diagnostics_checksum"] == second["strategic_drift_diagnostics_checksum"]


def test_each_drift_class_reachable():
    assert diagnose_strategic_drift(["stable", "stable"])["drift_class"] == "stable"
    assert diagnose_strategic_drift(["stable", "stressed"])["drift_class"] == "drifting"
    assert diagnose_strategic_drift(["stable", "transitional", "distorted"], ["deteriorated", "destabilized"])["drift_class"] == "deteriorating"
    assert diagnose_strategic_drift(["degraded", "fragile", "transitional"], ["improved", "recovering"])["drift_class"] == "recovering"
    assert diagnose_strategic_drift(["stable", "stressed", "stable", "stressed"])["drift_class"] == "oscillating"
    assert diagnose_strategic_drift(["stressed", "structurally_blocked"])["drift_class"] == "blocked"
    assert diagnose_strategic_drift(["stable"])["drift_class"] == "insufficient_history"
    assert diagnose_strategic_drift(["stable", "unknown"])["drift_class"] == "invalid_drift_input"


def test_malformed_non_list_input_invalid():
    assert diagnose_strategic_drift("stable", [])["drift_class"] == "invalid_drift_input"
    assert diagnose_strategic_drift(["stable", "stable"], "unchanged")["drift_class"] == "invalid_drift_input"


def test_invalid_state_and_invalid_transition_invalid():
    assert diagnose_strategic_drift(["stable", "bad_state"])["drift_class"] == "invalid_drift_input"
    assert diagnose_strategic_drift(["stable", "stable"], ["bad_transition"])["drift_class"] == "invalid_drift_input"


def test_insufficient_history_handling():
    result = diagnose_strategic_drift([_s("stable")])
    assert result["drift_class"] == "insufficient_history"
    assert result["state_count"] == 1


def test_blocked_latest_state_or_transition_handling():
    assert diagnose_strategic_drift(["stable", "structurally_blocked"])["drift_class"] == "blocked"
    assert diagnose_strategic_drift(["stable", "stressed"], ["blocked"])["drift_class"] == "blocked"


def test_oscillating_direction_change_handling():
    result = diagnose_strategic_drift(["stable", "stressed", "stable", "stressed"])
    assert result["drift_class"] == "oscillating"
    assert result["direction_change_count"] >= 2


def test_deteriorating_trend_handling():
    result = diagnose_strategic_drift(["stable", "transitional", "distorted"])
    assert result["drift_class"] == "deteriorating"


def test_recovering_trend_handling():
    result = diagnose_strategic_drift(["degraded", "fragile", "transitional"])
    assert result["drift_class"] == "recovering"


def test_drifting_mixed_movement_handling():
    result = diagnose_strategic_drift(["stable", "stressed"], ["unchanged", "deteriorated"])
    assert result["drift_class"] == "drifting"


def test_stable_no_movement_handling():
    result = diagnose_strategic_drift(["stressed", "stressed"], ["unchanged"])
    assert result["drift_class"] == "stable"


def test_fixed_template_explanation_and_invariants():
    result = diagnose_strategic_drift(["stable", "stable"])
    assert result["explanation"].startswith("Strategic drift diagnostics is deterministic:")
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
    states = [_s("stable"), _s("stressed")]
    transitions = [_t("deteriorated")]
    states_snapshot = deepcopy(states)
    transitions_snapshot = deepcopy(transitions)
    diagnose_strategic_drift(states, transitions)
    assert states == states_snapshot
    assert transitions == transitions_snapshot


def test_public_api_export():
    from transmission_layers.intelligence import tier7

    assert hasattr(tier7, "diagnose_strategic_drift")


def test_tier7a_and_tier7b_non_regression_smoke_checks():
    graph_result = classify_strategic_graph_state(
        {
            "nodes": [{"node_id": "A"}, {"node_id": "B"}],
            "edges": [{"source_node_id": "A", "target_node_id": "B", "edge_quality_score": 1.0}],
            "graph_health_score": 0.9,
        }
    )
    transition_result = assess_strategic_state_transition(_s("stable"), _s("stressed"))

    assert graph_result["strategic_graph_state"] == "stable"
    assert transition_result["transition_class"] == "deteriorated"


def test_tier4_5_6_operational_non_regression_smoke_checks_if_practical():
    from pathlib import Path

    from transmission_layers.intelligence.tier4.structural_entropy import compute_structural_entropy
    from transmission_layers.intelligence.tier5.federation_determinism import stable_checksum
    from transmission_layers.intelligence.tier6.transmission_explainability import assess_transmission_explainability
    from transmission_layers.operationalization.audit_summary import build_operational_audit_summary

    assert "entropy_score" in compute_structural_entropy([{"node_id": "A", "stress": 0.2}])
    assert stable_checksum({"x": 1}, prefix="smoke").startswith("smoke_")
    assert "explanation" in assess_transmission_explainability({"status": "ok"})
    assert "audit_summary" in build_operational_audit_summary({}, Path("/tmp/tier7c-smoke"), overwrite=False)
