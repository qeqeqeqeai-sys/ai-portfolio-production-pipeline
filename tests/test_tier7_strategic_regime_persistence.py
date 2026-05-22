from copy import deepcopy

from transmission_layers.intelligence.tier7 import assess_strategic_regime_persistence


def _s(label: str):
    return {"strategic_graph_state": label}


def _t(label: str):
    return {"transition_class": label}


def _d(label: str):
    return {"drift_class": label}


def _c(label: str):
    return {"continuity_class": label}


def test_deterministic_repeated_output_and_checksum_stability():
    states = [_s("stable"), _s("stressed"), _s("transitional")]
    transitions = [_t("deteriorated"), _t("deteriorated")]
    first = assess_strategic_regime_persistence(states, transitions, _d("deteriorating"), _c("degrading_continuity"))
    second = assess_strategic_regime_persistence(states, transitions, _d("deteriorating"), _c("degrading_continuity"))
    assert first == second
    assert first["strategic_regime_persistence_checksum"] == second["strategic_regime_persistence_checksum"]


def test_each_regime_persistence_class_reachable():
    assert assess_strategic_regime_persistence(["stable", "stable", "stable"])["regime_persistence_class"] == "persistent_regime"
    assert assess_strategic_regime_persistence(["stable", "stressed", "stressed"])["regime_persistence_class"] == "weakly_persistent_regime"
    assert assess_strategic_regime_persistence(["stable", "stable", "distorted"])["regime_persistence_class"] == "unstable_regime"
    assert assess_strategic_regime_persistence(["stable", "stressed", "stable", "stressed"])["regime_persistence_class"] == "shifting_regime"
    assert assess_strategic_regime_persistence(["stable", "transitional", "distorted"], ["deteriorated", "destabilized"])["regime_persistence_class"] == "degrading_regime"
    assert assess_strategic_regime_persistence(["degraded", "fragile", "transitional"], ["improved", "recovering"])["regime_persistence_class"] == "recovering_regime"
    assert assess_strategic_regime_persistence(["stable", "stressed", "structurally_blocked"])["regime_persistence_class"] == "blocked_regime"
    assert assess_strategic_regime_persistence(["stable", "stable"])["regime_persistence_class"] == "insufficient_history"
    assert assess_strategic_regime_persistence("bad")["regime_persistence_class"] == "invalid_regime_input"


def test_invalid_inputs_and_specific_handlers():
    assert assess_strategic_regime_persistence(["stable", "stable", "unknown"])["regime_persistence_class"] == "invalid_regime_input"
    assert assess_strategic_regime_persistence(["stable", "stable", "stable"], ["bad_transition"])["regime_persistence_class"] == "invalid_regime_input"
    assert assess_strategic_regime_persistence(["stable", "stable", "stable"], [], "bad_drift")["regime_persistence_class"] == "invalid_regime_input"
    assert assess_strategic_regime_persistence(["stable", "stable", "stable"], [], None, "bad_continuity")["regime_persistence_class"] == "invalid_regime_input"


def test_dominant_state_and_band_determinism_and_mixed_band_counting():
    result = assess_strategic_regime_persistence(["stable", "stressed", "stable", "transitional", "distorted"])
    assert result["dominant_state"] == "stable"
    assert result["dominant_regime_band"] == "stable_band"
    assert result["mixed_regime_band_count"] == 3


def test_fixed_template_explanation_and_invariants_and_immutable_inputs():
    states = [_s("stable"), _s("stable"), _s("stable")]
    transitions = [_t("unchanged")]
    drift = _d("stable")
    continuity = _c("continuous")
    ss, ts, ds, cs = deepcopy(states), deepcopy(transitions), deepcopy(drift), deepcopy(continuity)
    result = assess_strategic_regime_persistence(states, transitions, drift, continuity)
    assert result["explanation"].startswith("Strategic regime persistence intelligence is deterministic:")
    assert states == ss and transitions == ts and drift == ds and continuity == cs
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


def test_public_api_export_and_non_regression_smokes():
    from pathlib import Path

    from transmission_layers.intelligence import tier7
    from transmission_layers.intelligence.tier4.structural_entropy import compute_structural_entropy
    from transmission_layers.intelligence.tier5.federation_determinism import stable_checksum
    from transmission_layers.intelligence.tier6.transmission_explainability import assess_transmission_explainability
    from transmission_layers.intelligence.tier7 import (
        assess_strategic_continuity,
        assess_strategic_state_transition,
        classify_strategic_graph_state,
        diagnose_strategic_drift,
    )
    from transmission_layers.operationalization.audit_summary import build_operational_audit_summary

    assert hasattr(tier7, "assess_strategic_regime_persistence")
    assert classify_strategic_graph_state({"nodes": [{"node_id": "A"}], "edges": []})["strategic_graph_state"] == "stable"
    assert assess_strategic_state_transition(_s("stable"), _s("stressed"))["transition_class"] == "deteriorated"
    assert diagnose_strategic_drift(["stable", "stressed"])["drift_class"] == "drifting"
    assert assess_strategic_continuity(["stable", "stressed"])["continuity_class"] == "weakly_continuous"
    assert "entropy_score" in compute_structural_entropy([{"node_id": "A", "stress": 0.2}])
    assert stable_checksum({"x": 1}, prefix="smoke").startswith("smoke_")
    assert "explanation" in assess_transmission_explainability({"status": "ok"})
    assert "audit_summary" in build_operational_audit_summary({}, Path("/tmp/tier7e-smoke"), overwrite=False)
