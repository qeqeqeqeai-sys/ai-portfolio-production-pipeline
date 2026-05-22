from copy import deepcopy

from transmission_layers.intelligence.tier7 import assess_strategic_coherence


def test_deterministic_repeated_output_and_checksum_stability():
    kw = dict(
        strategic_state_assessment="stable",
        transition_assessment="unchanged",
        drift_diagnostics="stable",
        continuity_assessment="continuous",
        regime_persistence_assessment="persistent_regime",
        anomaly_attribution="no_anomaly",
    )
    a = assess_strategic_coherence(**kw)
    b = assess_strategic_coherence(**kw)
    assert a == b
    assert a["strategic_coherence_checksum"] == b["strategic_coherence_checksum"]


def test_invalid_inputs():
    assert assess_strategic_coherence({})["coherence_class"] == "invalid_coherence_input"
    assert assess_strategic_coherence("stable", transition_assessment="bad")["coherence_class"] == "invalid_coherence_input"
    assert assess_strategic_coherence("stable", drift_diagnostics="bad")["coherence_class"] == "invalid_coherence_input"
    assert assess_strategic_coherence("stable", continuity_assessment="bad")["coherence_class"] == "invalid_coherence_input"
    assert assess_strategic_coherence("stable", regime_persistence_assessment="bad")["coherence_class"] == "invalid_coherence_input"
    assert assess_strategic_coherence("stable", anomaly_attribution="bad")["coherence_class"] == "invalid_coherence_input"


def test_insufficient_context():
    assert assess_strategic_coherence("stable")["coherence_class"] == "insufficient_context"


def test_blocked_coherence():
    out = assess_strategic_coherence("stable", transition_assessment="blocked")
    assert out["coherence_class"] == "blocked_coherence"


def test_contradictory():
    out = assess_strategic_coherence("stable", anomaly_attribution="degradation_anomaly")
    assert out["coherence_class"] == "contradictory"


def test_incoherent_multiple_mismatches():
    out = assess_strategic_coherence(
        "stable", transition_assessment="improved", drift_diagnostics="deteriorating", anomaly_attribution="no_anomaly"
    )
    assert out["coherence_class"] == "incoherent"
    assert out["mismatch_count"] >= 2


def test_weakly_coherent_one_mismatch():
    out = assess_strategic_coherence("stable", drift_diagnostics="drifting", anomaly_attribution="no_anomaly")
    assert out["coherence_class"] == "weakly_coherent"
    assert out["mismatch_count"] == 1


def test_coherent():
    out = assess_strategic_coherence(
        "stable", "unchanged", "stable", "continuous", "persistent_regime", "no_anomaly"
    )
    assert out["coherence_class"] == "coherent"


def test_signal_ordering_and_template_and_invariants_and_immutability_and_export():
    in_state = {"strategic_graph_state": "stable"}
    in_drift = {"drift_class": "drifting"}
    original_state = deepcopy(in_state)
    original_drift = deepcopy(in_drift)
    out = assess_strategic_coherence(
        in_state,
        transition_assessment="deteriorated",
        drift_diagnostics=in_drift,
        continuity_assessment="weakly_continuous",
        regime_persistence_assessment="weakly_persistent_regime",
        anomaly_attribution="no_anomaly",
    )
    assert in_state == original_state
    assert in_drift == original_drift
    assert out["contradiction_signals"] == sorted(out["contradiction_signals"], key=out["contradiction_signals"].index)
    assert out["mismatch_signals"] == sorted(out["mismatch_signals"], key=out["mismatch_signals"].index)
    assert out["fixed_template_explanation"].startswith("Strategic coherence intelligence is deterministic:")
    assert out["invariant_flags"]["no_runtime_mutation"] is True


def test_all_classes_reachable():
    seen = {
        assess_strategic_coherence({})["coherence_class"],
        assess_strategic_coherence("stable")["coherence_class"],
        assess_strategic_coherence("stable", transition_assessment="blocked")["coherence_class"],
        assess_strategic_coherence("stable", anomaly_attribution="degradation_anomaly")["coherence_class"],
        assess_strategic_coherence("stable", drift_diagnostics="drifting", anomaly_attribution="no_anomaly")["coherence_class"],
        assess_strategic_coherence("stable", transition_assessment="improved", drift_diagnostics="deteriorating", anomaly_attribution="no_anomaly")["coherence_class"],
        assess_strategic_coherence("stable", "unchanged", "stable", "continuous", "persistent_regime", "no_anomaly")["coherence_class"],
    }
    assert seen == {
        "coherent",
        "weakly_coherent",
        "incoherent",
        "contradictory",
        "blocked_coherence",
        "insufficient_context",
        "invalid_coherence_input",
    }
