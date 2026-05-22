from copy import deepcopy

from transmission_layers.intelligence.tier7 import attribute_strategic_anomaly


def _s(label: str):
    return {"strategic_graph_state": label}


def _t(label: str):
    return {"transition_class": label}


def _d(label: str):
    return {"drift_class": label}


def _c(label: str):
    return {"continuity_class": label}


def _r(label: str):
    return {"regime_persistence_class": label}


def test_deterministic_repeated_output_and_checksum_stability():
    args = (["stable", "stressed", "transitional"], ["deteriorated", "destabilized"], "deteriorating", "degrading_continuity", "degrading_regime", {"k": 1})
    first = attribute_strategic_anomaly(*args)
    second = attribute_strategic_anomaly(*args)
    assert first == second
    assert first["strategic_anomaly_attribution_checksum"] == second["strategic_anomaly_attribution_checksum"]


def test_each_anomaly_attribution_class_reachable():
    assert attribute_strategic_anomaly(["stable"])["anomaly_attribution_class"] == "no_anomaly"
    assert attribute_strategic_anomaly(["stressed", "transitional"])["anomaly_attribution_class"] == "stress_anomaly"
    assert attribute_strategic_anomaly(["stable", "stressed"], ["destabilized"])["anomaly_attribution_class"] == "transition_anomaly"
    assert attribute_strategic_anomaly(["stable", "stressed"], drift_diagnostics="oscillating")["anomaly_attribution_class"] == "drift_anomaly"
    assert attribute_strategic_anomaly(["stable", "stressed"], continuity_assessment="interrupted")["anomaly_attribution_class"] == "continuity_anomaly"
    assert attribute_strategic_anomaly(["stable", "regime_shifting"])["anomaly_attribution_class"] == "regime_anomaly"
    assert attribute_strategic_anomaly(["stable", "fragmented"])["anomaly_attribution_class"] == "fragmentation_anomaly"
    assert attribute_strategic_anomaly(["stable", "distorted"])["anomaly_attribution_class"] == "distortion_anomaly"
    assert attribute_strategic_anomaly(["stable", "degraded"])["anomaly_attribution_class"] == "degradation_anomaly"
    assert attribute_strategic_anomaly(["stable", "structurally_blocked"])["anomaly_attribution_class"] == "blocked_anomaly"
    assert attribute_strategic_anomaly("bad")["anomaly_attribution_class"] == "invalid_anomaly_input"


def test_invalid_input_handlers():
    assert attribute_strategic_anomaly("bad")["anomaly_attribution_class"] == "invalid_anomaly_input"
    assert attribute_strategic_anomaly(["unknown"])["anomaly_attribution_class"] == "invalid_anomaly_input"
    assert attribute_strategic_anomaly(["stable"], ["unknown"])["anomaly_attribution_class"] == "invalid_anomaly_input"
    assert attribute_strategic_anomaly(["stable"], drift_diagnostics="unknown")["anomaly_attribution_class"] == "invalid_anomaly_input"
    assert attribute_strategic_anomaly(["stable"], continuity_assessment="unknown")["anomaly_attribution_class"] == "invalid_anomaly_input"
    assert attribute_strategic_anomaly(["stable"], regime_persistence_assessment="unknown")["anomaly_attribution_class"] == "invalid_anomaly_input"


def test_triggering_factors_order_and_fixed_template_and_immutability_and_flags_and_export_and_smokes():
    states = [_s("stable"), _s("stressed")]
    transitions = [_t("deteriorated")]
    drift = _d("drifting")
    continuity = _c("weakly_continuous")
    regime = _r("weakly_persistent_regime")
    evidence = {"b": 2, "a": 1}
    ss, ts, ds, cs, rs, es = deepcopy(states), deepcopy(transitions), deepcopy(drift), deepcopy(continuity), deepcopy(regime), deepcopy(evidence)

    result = attribute_strategic_anomaly(states, transitions, drift, continuity, regime, evidence)
    assert result["fixed_template_explanation"].startswith("Strategic anomaly attribution intelligence is deterministic:")
    assert result["triggering_factors"] == [
        "transition_majority_deterioration_condition",
        "decision:rule_10_transition_majority_deterioration_condition",
    ]
    assert states == ss and transitions == ts and drift == ds and continuity == cs and regime == rs and evidence == es
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

    from pathlib import Path
    from transmission_layers.intelligence import tier7
    from transmission_layers.intelligence.tier4.structural_entropy import compute_structural_entropy
    from transmission_layers.intelligence.tier5.federation_determinism import stable_checksum
    from transmission_layers.intelligence.tier6.transmission_explainability import assess_transmission_explainability
    from transmission_layers.operationalization.audit_summary import build_operational_audit_summary

    assert hasattr(tier7, "attribute_strategic_anomaly")
    assert "entropy_score" in compute_structural_entropy([{"node_id": "A", "stress": 0.2}])
    assert stable_checksum({"x": 1}, prefix="smoke").startswith("smoke_")
    assert "explanation" in assess_transmission_explainability({"status": "ok"})
    assert "audit_summary" in build_operational_audit_summary({}, Path("/tmp/tier7f-smoke"), overwrite=False)
