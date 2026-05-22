from copy import deepcopy

from transmission_layers.intelligence.tier7 import assess_strategic_continuity


def _s(label: str):
    return {"strategic_graph_state": label}


def _t(label: str):
    return {"transition_class": label}


def _d(label: str):
    return {"drift_class": label}


def test_deterministic_repeated_output_and_checksum_stability():
    states = [_s("stable"), _s("stressed")]
    transitions = [_t("deteriorated")]
    first = assess_strategic_continuity(states, transitions, _d("drifting"))
    second = assess_strategic_continuity(states, transitions, _d("drifting"))
    assert first == second
    assert first["strategic_continuity_checksum"] == second["strategic_continuity_checksum"]


def test_each_continuity_class_reachable():
    assert assess_strategic_continuity(["stable", "stable"])["continuity_class"] == "continuous"
    assert assess_strategic_continuity(["stable", "stressed"])["continuity_class"] == "weakly_continuous"
    assert assess_strategic_continuity(["stable", "degraded"])["continuity_class"] == "interrupted"
    assert assess_strategic_continuity(["stable", "transitional", "distorted"], ["deteriorated", "destabilized"])["continuity_class"] == "degrading_continuity"
    assert assess_strategic_continuity(["degraded", "fragile", "transitional"], ["improved", "recovering"])["continuity_class"] == "recovering_continuity"
    assert assess_strategic_continuity(["stable", "stressed", "stable", "stressed"])["continuity_class"] == "oscillating_continuity"
    assert assess_strategic_continuity(["stable", "structurally_blocked"])["continuity_class"] == "blocked_continuity"
    assert assess_strategic_continuity(["stable"])["continuity_class"] == "insufficient_history"
    assert assess_strategic_continuity("bad")["continuity_class"] == "invalid_continuity_input"


def test_invalid_state_transition_and_drift_invalid():
    assert assess_strategic_continuity(["stable", "unknown"])["continuity_class"] == "invalid_continuity_input"
    assert assess_strategic_continuity(["stable", "stable"], ["bad_transition"])["continuity_class"] == "invalid_continuity_input"
    assert assess_strategic_continuity(["stable", "stable"], [], "bad_drift")["continuity_class"] == "invalid_continuity_input"


def test_precedence_blocked_over_degrading_and_recovering():
    result = assess_strategic_continuity(["stable", "structurally_blocked"], ["destabilized"], "deteriorating")
    assert result["continuity_class"] == "blocked_continuity"


def test_fixed_template_explanation_and_invariants():
    result = assess_strategic_continuity(["stable", "stable"])
    assert result["explanation"].startswith("Strategic continuity intelligence is deterministic:")
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
    drift = _d("drifting")
    ss = deepcopy(states)
    ts = deepcopy(transitions)
    ds = deepcopy(drift)
    assess_strategic_continuity(states, transitions, drift)
    assert states == ss
    assert transitions == ts
    assert drift == ds


def test_public_api_export_and_non_regression_smokes():
    from pathlib import Path

    from transmission_layers.intelligence import tier7
    from transmission_layers.intelligence.tier4.structural_entropy import compute_structural_entropy
    from transmission_layers.intelligence.tier5.federation_determinism import stable_checksum
    from transmission_layers.intelligence.tier6.transmission_explainability import assess_transmission_explainability
    from transmission_layers.intelligence.tier7 import (
        assess_strategic_state_transition,
        classify_strategic_graph_state,
        diagnose_strategic_drift,
    )
    from transmission_layers.operationalization.audit_summary import build_operational_audit_summary

    assert hasattr(tier7, "assess_strategic_continuity")
    assert classify_strategic_graph_state({"nodes": [{"node_id": "A"}], "edges": []})["strategic_graph_state"] == "stable"
    assert assess_strategic_state_transition(_s("stable"), _s("stressed"))["transition_class"] == "deteriorated"
    assert diagnose_strategic_drift(["stable", "stressed"])["drift_class"] == "drifting"
    assert "entropy_score" in compute_structural_entropy([{"node_id": "A", "stress": 0.2}])
    assert stable_checksum({"x": 1}, prefix="smoke").startswith("smoke_")
    assert "explanation" in assess_transmission_explainability({"status": "ok"})
    assert "audit_summary" in build_operational_audit_summary({}, Path("/tmp/tier7d-smoke"), overwrite=False)
