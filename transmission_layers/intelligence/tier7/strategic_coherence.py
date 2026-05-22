"""Tier 7G deterministic strategic coherence intelligence."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Mapping, Tuple

from transmission_layers.operationalization.serialization import stable_checksum
from .strategic_anomaly_attribution import ANOMALY_ATTRIBUTION_CLASSES
from .strategic_continuity import CONTINUITY_CLASSES
from .strategic_drift_diagnostics import DRIFT_CLASSES
from .strategic_graph_state import STRATEGIC_STATES
from .strategic_regime_persistence import REGIME_PERSISTENCE_CLASSES
from .strategic_state_transition import SEVERITY_RANKS, TRANSITION_CLASSES

COHERENCE_CLASSES: Tuple[str, ...] = (
    "coherent",
    "weakly_coherent",
    "incoherent",
    "contradictory",
    "blocked_coherence",
    "insufficient_context",
    "invalid_coherence_input",
)

COHERENCE_PRECEDENCE: Tuple[str, ...] = (
    "rule_1_invalid_inputs",
    "rule_2_insufficient_context",
    "rule_3_blocked_coherence",
    "rule_4_contradictions",
    "rule_5_multiple_mismatches",
    "rule_6_single_mismatch",
    "rule_7_default_coherent",
)


def _extract(payload: Any, key: str) -> str | None:
    if isinstance(payload, Mapping):
        value = payload.get(key)
        return value if isinstance(value, str) else None
    return payload if isinstance(payload, str) else None


def assess_strategic_coherence(
    strategic_state_assessment: Any,
    transition_assessment: Any | None = None,
    drift_diagnostics: Any | None = None,
    continuity_assessment: Any | None = None,
    regime_persistence_assessment: Any | None = None,
    anomaly_attribution: Any | None = None,
) -> Dict[str, Any]:
    state_safe = deepcopy(strategic_state_assessment)
    transition_safe = deepcopy(transition_assessment)
    drift_safe = deepcopy(drift_diagnostics)
    continuity_safe = deepcopy(continuity_assessment)
    regime_safe = deepcopy(regime_persistence_assessment)
    anomaly_safe = deepcopy(anomaly_attribution)

    state = _extract(state_safe, "strategic_graph_state")
    transition = _extract(transition_safe, "transition_class")
    drift = _extract(drift_safe, "drift_class")
    continuity = _extract(continuity_safe, "continuity_class")
    regime = _extract(regime_safe, "regime_persistence_class")
    anomaly = _extract(anomaly_safe, "anomaly_attribution_class")

    invalid = (
        state not in STRATEGIC_STATES
        or (transition_assessment is not None and transition not in TRANSITION_CLASSES)
        or (drift_diagnostics is not None and drift not in DRIFT_CLASSES)
        or (continuity_assessment is not None and continuity not in CONTINUITY_CLASSES)
        or (regime_persistence_assessment is not None and regime not in REGIME_PERSISTENCE_CLASSES)
        or (anomaly_attribution is not None and anomaly not in ANOMALY_ATTRIBUTION_CLASSES)
    )

    optional_missing = all(x is None for x in (transition, drift, continuity, regime, anomaly))

    blocked = (
        state == "structurally_blocked"
        or transition == "blocked"
        or drift == "blocked"
        or continuity == "blocked_continuity"
        or regime == "blocked_regime"
        or anomaly == "blocked_anomaly"
    )

    contradiction_checks = [
        ("stable_with_severe_anomaly", state == "stable" and anomaly in {"degradation_anomaly", "fragmentation_anomaly", "distortion_anomaly", "blocked_anomaly", "regime_anomaly"}),
        ("blocked_state_with_no_anomaly", state == "structurally_blocked" and anomaly == "no_anomaly"),
        ("blocked_context_with_no_anomaly", (regime == "blocked_regime" or continuity == "blocked_continuity" or drift == "blocked") and anomaly == "no_anomaly"),
        ("persistent_regime_with_oscillating_drift", regime == "persistent_regime" and drift == "oscillating"),
        ("persistent_regime_with_interrupted_continuity", regime == "persistent_regime" and continuity == "interrupted"),
        ("continuous_with_deteriorating_drift", continuity == "continuous" and drift == "deteriorating"),
        ("no_anomaly_with_degrading_or_blocked_regime", anomaly == "no_anomaly" and regime in {"degrading_regime", "blocked_regime"}),
        ("no_anomaly_with_bad_transition", anomaly == "no_anomaly" and transition in {"deteriorated", "destabilized"}),
        ("stable_with_degrading_or_blocked_regime", state == "stable" and regime in {"degrading_regime", "blocked_regime"}),
        ("degraded_with_persistent_and_no_anomaly", state == "degraded" and regime == "persistent_regime" and anomaly == "no_anomaly"),
    ]
    contradiction_signals = [name for name, condition in contradiction_checks if condition]

    mismatch_checks = [
        ("stable_with_nonstable_transition", state == "stable" and transition in {"stressed", "deteriorated", "destabilized"}),
        ("stable_with_nonstable_drift", state == "stable" and drift in {"drifting", "deteriorating", "recovering", "oscillating"}),
        ("stable_with_noncontinuous_continuity", state == "stable" and continuity in {"weakly_continuous", "degrading_continuity", "recovering_continuity", "oscillating_continuity", "interrupted"}),
        ("stable_with_nonpersistent_regime", state == "stable" and regime in {"weakly_persistent_regime", "unstable_regime", "shifting_regime", "degrading_regime", "recovering_regime"}),
        ("nonstable_state_with_no_anomaly", state in {"stressed", "transitional", "regime_shifting", "distorted", "fragmented", "fragile", "degraded"} and anomaly == "no_anomaly"),
        ("severe_state_without_anomaly", state in {"degraded", "fragmented", "distorted", "fragile", "structurally_blocked"} and anomaly is None),
        ("regime_shifting_without_support", state == "regime_shifting" and regime != "shifting_regime" and anomaly != "regime_anomaly" and drift != "drifting"),
        ("degraded_fragmented_distorted_without_matching_context", state in {"degraded", "fragmented", "distorted"} and anomaly not in {"degradation_anomaly", "fragmentation_anomaly", "distortion_anomaly"} and regime != "degrading_regime"),
        ("recovering_transition_with_degrading_regime", transition == "recovering" and regime == "degrading_regime"),
        ("improved_transition_with_deteriorating_drift", transition == "improved" and drift == "deteriorating"),
        ("deteriorated_or_destabilized_transition_with_recovering_regime", transition in {"deteriorated", "destabilized"} and regime == "recovering_regime"),
    ]
    mismatch_signals = [name for name, condition in mismatch_checks if condition]

    if invalid:
        coherence_class, rule = "invalid_coherence_input", COHERENCE_PRECEDENCE[0]
    elif optional_missing:
        coherence_class, rule = "insufficient_context", COHERENCE_PRECEDENCE[1]
    elif blocked:
        coherence_class, rule = "blocked_coherence", COHERENCE_PRECEDENCE[2]
    elif contradiction_signals:
        coherence_class, rule = "contradictory", COHERENCE_PRECEDENCE[3]
    elif len(mismatch_signals) >= 2:
        coherence_class, rule = "incoherent", COHERENCE_PRECEDENCE[4]
    elif len(mismatch_signals) == 1:
        coherence_class, rule = "weakly_coherent", COHERENCE_PRECEDENCE[5]
    else:
        coherence_class, rule = "coherent", COHERENCE_PRECEDENCE[6]

    result = {
        "coherence_class": coherence_class,
        "strategic_graph_state": state,
        "transition_class": transition,
        "drift_class": drift,
        "continuity_class": continuity,
        "regime_persistence_class": regime,
        "anomaly_attribution_class": anomaly,
        "contradiction_signals": contradiction_signals,
        "mismatch_signals": mismatch_signals,
        "contradiction_count": len(contradiction_signals),
        "mismatch_count": len(mismatch_signals),
        "deterministic_evidence_summary": {
            "state_severity_rank": SEVERITY_RANKS.get(state, -1),
            "optional_context_missing": optional_missing,
            "blocked_condition": blocked,
            "applied_rule": rule,
        },
        "fixed_template_explanation": (
            "Strategic coherence intelligence is deterministic: "
            f"coherence_class={coherence_class}; strategic_graph_state={state}; transition_class={transition}; "
            f"drift_class={drift}; continuity_class={continuity}; regime_persistence_class={regime}; "
            f"anomaly_attribution_class={anomaly}; contradictions={len(contradiction_signals)}; "
            f"mismatches={len(mismatch_signals)}; applied_rule={rule}."
        ),
        "precedence_metadata": {
            "ordering": list(COHERENCE_PRECEDENCE),
            "applied_rule": rule,
            "severity_rank_ordering": dict(SEVERITY_RANKS),
        },
        "invariant_flags": {
            "deterministic_output": True,
            "replay_compatible": True,
            "immutable_input_safe": True,
            "no_runtime_mutation": True,
            "no_adaptive_control": True,
            "no_prediction_engine": True,
            "additive_only": True,
        },
    }
    result["strategic_coherence_checksum"] = stable_checksum(
        {k: result[k] for k in result if k != "strategic_coherence_checksum"},
        prefix="tier7g_strategic_coherence",
    )
    return result


__all__ = [
    "COHERENCE_CLASSES",
    "COHERENCE_PRECEDENCE",
    "assess_strategic_coherence",
]
