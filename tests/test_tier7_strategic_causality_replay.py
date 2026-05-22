from copy import deepcopy

from transmission_layers.intelligence.tier7 import (
    CAUSALITY_REPLAY_CLASSES,
    replay_strategic_causality,
)


def test_deterministic_repeated_output_and_checksum_stability():
    kw = dict(
        strategic_state_sequence=["stable", "stressed", "transitional"],
        transition_sequence=["deteriorated", "deteriorated"],
        coherence_assessment="coherent",
    )
    a = replay_strategic_causality(**kw)
    b = replay_strategic_causality(**kw)
    assert a == b
    assert a["strategic_causality_replay_checksum"] == b["strategic_causality_replay_checksum"]


def test_input_validation_and_insufficient_history():
    assert replay_strategic_causality("bad")["causality_replay_class"] == "invalid_causality_replay_input"
    assert replay_strategic_causality(["bad", "stable"])["causality_replay_class"] == "invalid_causality_replay_input"
    assert replay_strategic_causality(["stable", "stable"], transition_sequence=["bad"])["causality_replay_class"] == "invalid_causality_replay_input"
    assert replay_strategic_causality(["stable", "stable"], drift_diagnostics="bad")["causality_replay_class"] == "invalid_causality_replay_input"
    assert replay_strategic_causality(["stable", "stable"], continuity_assessment="bad")["causality_replay_class"] == "invalid_causality_replay_input"
    assert replay_strategic_causality(["stable", "stable"], regime_persistence_assessment="bad")["causality_replay_class"] == "invalid_causality_replay_input"
    assert replay_strategic_causality(["stable", "stable"], anomaly_attribution="bad")["causality_replay_class"] == "invalid_causality_replay_input"
    assert replay_strategic_causality(["stable", "stable"], coherence_assessment="bad")["causality_replay_class"] == "invalid_causality_replay_input"
    assert replay_strategic_causality(["stable", "stable"], stability_resilience_assessment="bad")["causality_replay_class"] == "invalid_causality_replay_input"
    assert replay_strategic_causality(["stable"])["causality_replay_class"] == "insufficient_replay_history"


def test_classifications_and_reachability():
    seen = {
        replay_strategic_causality("bad")["causality_replay_class"],
        replay_strategic_causality(["stable"])["causality_replay_class"],
        replay_strategic_causality(["stable", "structurally_blocked"])["causality_replay_class"],
        replay_strategic_causality(["stable", "stressed"], coherence_assessment="incoherent")["causality_replay_class"],
        replay_strategic_causality(["stable", "fragmented"])["causality_replay_class"],
        replay_strategic_causality(["stable", "degraded"])["causality_replay_class"],
        replay_strategic_causality(["stable", "stressed"], coherence_assessment="coherent")["causality_replay_class"],
        replay_strategic_causality(["stable", "stressed"])["causality_replay_class"],
        replay_strategic_causality(["stable", "stable"])["causality_replay_class"],
    }
    assert seen == set(CAUSALITY_REPLAY_CLASSES)


def test_deterministic_paths_explanation_immutability_and_flags_and_export():
    states = [{"strategic_graph_state": "stable"}, {"strategic_graph_state": "stressed"}, {"strategic_graph_state": "transitional"}]
    transitions = [{"transition_class": "deteriorated"}, {"transition_class": "deteriorated"}]
    evidence = [{"z": 1, "a": 2}, {"k": 3}]
    states_original = deepcopy(states)
    transitions_original = deepcopy(transitions)
    evidence_original = deepcopy(evidence)

    out = replay_strategic_causality(
        states,
        transition_sequence=transitions,
        drift_diagnostics={"drift_class": "drifting"},
        continuity_assessment={"continuity_class": "weakly_continuous"},
        regime_persistence_assessment={"regime_persistence_class": "weakly_persistent_regime"},
        anomaly_attribution={"anomaly_attribution_class": "stress_anomaly"},
        coherence_assessment={"coherence_class": "coherent"},
        stability_resilience_assessment={"stability_resilience_class": "weakly_stable"},
        structural_evidence_sequence=evidence,
    )

    assert states == states_original
    assert transitions == transitions_original
    assert evidence == evidence_original
    assert out["causal_replay_steps"] == sorted(out["causal_replay_steps"], key=lambda s: s["step_index"])
    assert out["causal_factor_path"] == sorted(out["causal_factor_path"], key=out["causal_factor_path"].index)
    assert out["fixed_template_explanation"].startswith("Strategic causality replay intelligence is deterministic:")
    assert out["invariant_flags"]["no_runtime_mutation"] is True


def test_tier7_and_lower_tier_non_regression_smoke():
    from transmission_layers.intelligence.tier7 import classify_strategic_graph_state, assess_strategic_state_transition
    from transmission_layers.intelligence.tier4.causal_replay import replay_causal_influence

    s = classify_strategic_graph_state({"nodes": [], "edges": []})
    t = assess_strategic_state_transition("stable", "stressed")
    r = replay_causal_influence({"node_metrics": [], "corridor_metrics": [], "health_state": "stable"}, {"node_metrics": [], "corridor_metrics": [], "health_state": "stable"})
    assert "strategic_graph_state" in s
    assert "transition_class" in t
    assert isinstance(r, dict)
