from copy import deepcopy

from transmission_layers.intelligence.tier7 import (
    STABILITY_RESILIENCE_CLASSES,
    assess_strategic_stability_resilience,
)


def test_deterministic_repeated_output_and_checksum_stability():
    kw = dict(
        strategic_state_sequence=["stable", "stable", "stable"],
        transition_sequence=["unchanged", "unchanged"],
        drift_diagnostics="stable",
        continuity_assessment="continuous",
        regime_persistence_assessment="persistent_regime",
        anomaly_attribution="no_anomaly",
        coherence_assessment="coherent",
    )
    a = assess_strategic_stability_resilience(**kw)
    b = assess_strategic_stability_resilience(**kw)
    assert a == b
    assert a["strategic_stability_resilience_checksum"] == b["strategic_stability_resilience_checksum"]


def test_validation_failures_invalid_input():
    assert assess_strategic_stability_resilience("bad")["stability_resilience_class"] == "invalid_stability_input"
    assert assess_strategic_stability_resilience(["stable"] * 3, transition_sequence=["bad"])["stability_resilience_class"] == "invalid_stability_input"
    assert assess_strategic_stability_resilience(["bad"] * 3)["stability_resilience_class"] == "invalid_stability_input"
    assert assess_strategic_stability_resilience(["stable"] * 3, drift_diagnostics="bad")["stability_resilience_class"] == "invalid_stability_input"
    assert assess_strategic_stability_resilience(["stable"] * 3, continuity_assessment="bad")["stability_resilience_class"] == "invalid_stability_input"
    assert assess_strategic_stability_resilience(["stable"] * 3, regime_persistence_assessment="bad")["stability_resilience_class"] == "invalid_stability_input"
    assert assess_strategic_stability_resilience(["stable"] * 3, anomaly_attribution="bad")["stability_resilience_class"] == "invalid_stability_input"
    assert assess_strategic_stability_resilience(["stable"] * 3, coherence_assessment="bad")["stability_resilience_class"] == "invalid_stability_input"


def test_insufficient_history():
    assert assess_strategic_stability_resilience(["stable", "stable"])["stability_resilience_class"] == "insufficient_history"


def test_classifications_and_reachability():
    seen = {
        assess_strategic_stability_resilience("bad")["stability_resilience_class"],
        assess_strategic_stability_resilience(["stable", "stable"])["stability_resilience_class"],
        assess_strategic_stability_resilience(["stable", "stable", "structurally_blocked"])["stability_resilience_class"],
        assess_strategic_stability_resilience(["stable", "stable", "stable"], coherence_assessment="incoherent")["stability_resilience_class"],
        assess_strategic_stability_resilience(["stable", "stable", "degraded"])["stability_resilience_class"],
        assess_strategic_stability_resilience(["stable", "stable", "fragile"])["stability_resilience_class"],
        assess_strategic_stability_resilience(["stable", "stable", "stressed"], continuity_assessment="weakly_continuous")["stability_resilience_class"],
        assess_strategic_stability_resilience(["stable", "stable", "stable"], transition_sequence=["unchanged"], drift_diagnostics="stable", continuity_assessment="continuous", regime_persistence_assessment="persistent_regime", anomaly_attribution="no_anomaly", coherence_assessment="coherent")["stability_resilience_class"],
        assess_strategic_stability_resilience(["stable", "stable", "stable"], continuity_assessment="recovering_continuity", coherence_assessment="coherent")["stability_resilience_class"],
    }
    assert seen == set(STABILITY_RESILIENCE_CLASSES)


def test_factor_ordering_template_immutability_and_flags_and_export():
    states = [{"strategic_graph_state": "stable"}, {"strategic_graph_state": "stable"}, {"strategic_graph_state": "stable"}]
    transitions = [{"transition_class": "unchanged"}, {"transition_class": "unchanged"}]
    evidence = {"z": 1, "a": 2}
    states_original = deepcopy(states)
    transitions_original = deepcopy(transitions)
    evidence_original = deepcopy(evidence)

    out = assess_strategic_stability_resilience(
        states,
        transition_sequence=transitions,
        drift_diagnostics={"drift_class": "stable"},
        continuity_assessment={"continuity_class": "continuous"},
        regime_persistence_assessment={"regime_persistence_class": "persistent_regime"},
        anomaly_attribution={"anomaly_attribution_class": "no_anomaly"},
        coherence_assessment={"coherence_class": "coherent"},
        structural_evidence=evidence,
    )

    assert states == states_original
    assert transitions == transitions_original
    assert evidence == evidence_original
    assert out["fixed_template_explanation"].startswith("Strategic stability/resilience intelligence is deterministic:")
    assert out["resilience_factors"] == sorted(out["resilience_factors"], key=out["resilience_factors"].index)
    assert out["risk_factors"] == sorted(out["risk_factors"], key=out["risk_factors"].index)
    assert out["invariant_flags"]["no_runtime_mutation"] is True
