"""Tier 7F deterministic strategic anomaly attribution intelligence."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Mapping, Tuple

from transmission_layers.operationalization.serialization import stable_checksum
from .strategic_continuity import CONTINUITY_CLASSES
from .strategic_drift_diagnostics import DRIFT_CLASSES
from .strategic_graph_state import STRATEGIC_STATES
from .strategic_regime_persistence import REGIME_PERSISTENCE_CLASSES
from .strategic_state_transition import SEVERITY_RANKS, TRANSITION_CLASSES

ANOMALY_ATTRIBUTION_CLASSES: Tuple[str, ...] = (
    "no_anomaly",
    "stress_anomaly",
    "transition_anomaly",
    "drift_anomaly",
    "continuity_anomaly",
    "regime_anomaly",
    "fragmentation_anomaly",
    "distortion_anomaly",
    "degradation_anomaly",
    "blocked_anomaly",
    "invalid_anomaly_input",
)

ANOMALY_PRECEDENCE: Tuple[str, ...] = (
    "rule_1_malformed_non_list_state_input",
    "rule_2_invalid_state_or_transition_or_drift_or_continuity_or_regime",
    "rule_3_blocked_condition",
    "rule_4_degradation_condition",
    "rule_5_fragmentation_condition",
    "rule_6_distortion_condition",
    "rule_7_oscillation_drift_condition",
    "rule_8_continuity_disruption_condition",
    "rule_9_regime_shift_condition",
    "rule_10_transition_majority_deterioration_condition",
    "rule_11_stress_or_transitional_dominance_condition",
    "rule_12_default_no_anomaly",
)


def _extract_state(item: Any) -> str | None:
    if isinstance(item, Mapping):
        value = item.get("strategic_graph_state")
        return value if isinstance(value, str) else None
    return item if isinstance(item, str) else None


def _extract_transition(item: Any) -> str | None:
    if isinstance(item, Mapping):
        value = item.get("transition_class")
        return value if isinstance(value, str) else None
    return item if isinstance(item, str) else None


def _extract_drift(item: Any) -> str | None:
    if isinstance(item, Mapping):
        value = item.get("drift_class")
        return value if isinstance(value, str) else None
    return item if isinstance(item, str) else None


def _extract_continuity(item: Any) -> str | None:
    if isinstance(item, Mapping):
        value = item.get("continuity_class")
        return value if isinstance(value, str) else None
    return item if isinstance(item, str) else None


def _extract_regime(item: Any) -> str | None:
    if isinstance(item, Mapping):
        value = item.get("regime_persistence_class")
        return value if isinstance(value, str) else None
    return item if isinstance(item, str) else None


def attribute_strategic_anomaly(
    strategic_state_sequence: Any,
    transition_sequence: Any | None = None,
    drift_diagnostics: Any | None = None,
    continuity_assessment: Any | None = None,
    regime_persistence_assessment: Any | None = None,
    structural_evidence: Any | None = None,
) -> Dict[str, Any]:
    states_safe = deepcopy(strategic_state_sequence)
    transitions_safe = deepcopy(transition_sequence) if transition_sequence is not None else []
    drift_safe = deepcopy(drift_diagnostics)
    continuity_safe = deepcopy(continuity_assessment)
    regime_safe = deepcopy(regime_persistence_assessment)
    structural_evidence_safe = deepcopy(structural_evidence) if isinstance(structural_evidence, dict) else {}

    malformed_input = not isinstance(states_safe, list) or (
        transition_sequence is not None and not isinstance(transitions_safe, list)
    )

    state_path: List[str | None] = [_extract_state(s) for s in states_safe] if isinstance(states_safe, list) else []
    transition_path: List[str | None] = [_extract_transition(t) for t in transitions_safe] if isinstance(transitions_safe, list) else []
    drift_class = _extract_drift(drift_safe)
    continuity_class = _extract_continuity(continuity_safe)
    regime_class = _extract_regime(regime_safe)

    invalid_state_count = sum(1 for s in state_path if s not in STRATEGIC_STATES)
    invalid_transition_count = sum(1 for t in transition_path if t not in TRANSITION_CLASSES)
    invalid_drift_count = 0 if drift_safe is None or drift_class in DRIFT_CLASSES else 1
    invalid_continuity_count = 0 if continuity_safe is None or continuity_class in CONTINUITY_CLASSES else 1
    invalid_regime_count = 0 if regime_safe is None or regime_class in REGIME_PERSISTENCE_CLASSES else 1

    initial_state = state_path[0] if state_path else None
    latest_state = state_path[-1] if state_path else None
    severity_path = [SEVERITY_RANKS[s] for s in state_path if s in SEVERITY_RANKS]
    transition_class_path = [t for t in transition_path if isinstance(t, str)]

    state_counts: Dict[str, int] = {}
    for s in state_path:
        if isinstance(s, str):
            state_counts[s] = state_counts.get(s, 0) + 1

    dominant_state = (
        sorted(state_counts.items(), key=lambda x: (-x[1], SEVERITY_RANKS.get(x[0], 99), x[0]))[0][0]
        if state_counts
        else None
    )

    transition_counts: Dict[str, int] = {}
    for t in transition_path:
        if isinstance(t, str):
            transition_counts[t] = transition_counts.get(t, 0) + 1

    dominant_transition_class = (
        sorted(transition_counts.items(), key=lambda x: (-x[1], x[0]))[0][0] if transition_counts else None
    )

    worsening_transition_count = sum(1 for t in transition_path if t in {"destabilized", "deteriorated"})
    blocked_condition = latest_state == "structurally_blocked" or regime_class == "blocked_regime" or continuity_class == "blocked_continuity"
    degradation_condition = regime_class == "degrading_regime" or latest_state == "degraded" or dominant_state == "degraded"
    fragmentation_condition = latest_state == "fragmented" or dominant_state == "fragmented"
    distortion_condition = latest_state == "distorted" or dominant_state == "distorted"
    oscillation_condition = drift_class == "oscillating" or continuity_class == "oscillating_continuity"
    continuity_disruption_condition = continuity_class == "interrupted" or regime_class == "unstable_regime"
    regime_shift_condition = latest_state == "regime_shifting" or regime_class == "shifting_regime"
    transition_anomaly_condition = worsening_transition_count > (len(transition_path) / 2.0)
    stress_condition = dominant_state in {"stressed", "transitional"}

    if malformed_input:
        anomaly_class = "invalid_anomaly_input"
        decision_rule = ANOMALY_PRECEDENCE[0]
    elif (
        invalid_state_count > 0
        or invalid_transition_count > 0
        or invalid_drift_count > 0
        or invalid_continuity_count > 0
        or invalid_regime_count > 0
    ):
        anomaly_class = "invalid_anomaly_input"
        decision_rule = ANOMALY_PRECEDENCE[1]
    elif blocked_condition:
        anomaly_class = "blocked_anomaly"
        decision_rule = ANOMALY_PRECEDENCE[2]
    elif degradation_condition:
        anomaly_class = "degradation_anomaly"
        decision_rule = ANOMALY_PRECEDENCE[3]
    elif fragmentation_condition:
        anomaly_class = "fragmentation_anomaly"
        decision_rule = ANOMALY_PRECEDENCE[4]
    elif distortion_condition:
        anomaly_class = "distortion_anomaly"
        decision_rule = ANOMALY_PRECEDENCE[5]
    elif oscillation_condition:
        anomaly_class = "drift_anomaly"
        decision_rule = ANOMALY_PRECEDENCE[6]
    elif continuity_disruption_condition:
        anomaly_class = "continuity_anomaly"
        decision_rule = ANOMALY_PRECEDENCE[7]
    elif regime_shift_condition:
        anomaly_class = "regime_anomaly"
        decision_rule = ANOMALY_PRECEDENCE[8]
    elif transition_anomaly_condition:
        anomaly_class = "transition_anomaly"
        decision_rule = ANOMALY_PRECEDENCE[9]
    elif stress_condition:
        anomaly_class = "stress_anomaly"
        decision_rule = ANOMALY_PRECEDENCE[10]
    else:
        anomaly_class = "no_anomaly"
        decision_rule = ANOMALY_PRECEDENCE[11]

    triggering_factors = [
        factor
        for factor, condition in (
            ("malformed_state_input", malformed_input),
            ("invalid_state_class", invalid_state_count > 0),
            ("invalid_transition_class", invalid_transition_count > 0),
            ("invalid_drift_class", invalid_drift_count > 0),
            ("invalid_continuity_class", invalid_continuity_count > 0),
            ("invalid_regime_class", invalid_regime_count > 0),
            ("blocked_condition", blocked_condition),
            ("degradation_condition", degradation_condition),
            ("fragmentation_condition", fragmentation_condition),
            ("distortion_condition", distortion_condition),
            ("oscillation_condition", oscillation_condition),
            ("continuity_disruption_condition", continuity_disruption_condition),
            ("regime_shift_condition", regime_shift_condition),
            ("transition_majority_deterioration_condition", transition_anomaly_condition),
            ("stress_or_transitional_dominance_condition", stress_condition),
            (f"decision:{decision_rule}", True),
        )
        if condition
    ]

    evidence_summary = {
        "malformed_input": malformed_input,
        "invalid_state_count": invalid_state_count,
        "invalid_transition_count": invalid_transition_count,
        "invalid_drift_count": invalid_drift_count,
        "invalid_continuity_count": invalid_continuity_count,
        "invalid_regime_count": invalid_regime_count,
        "worsening_transition_count": worsening_transition_count,
        "structural_evidence_keys": sorted(str(k) for k in structural_evidence_safe.keys()),
    }

    explanation = (
        "Strategic anomaly attribution intelligence is deterministic: "
        f"anomaly_attribution_class={anomaly_class}; state_count={len(state_path)}; transition_count={len(transition_path)}; "
        f"initial_state={initial_state}; latest_state={latest_state}; dominant_state={dominant_state}; "
        f"drift_class={drift_class}; continuity_class={continuity_class}; regime_persistence_class={regime_class}; "
        f"decision_rule={decision_rule}."
    )

    result = {
        "anomaly_attribution_class": anomaly_class,
        "state_count": len(state_path),
        "transition_count": len(transition_path),
        "initial_state": initial_state,
        "latest_state": latest_state,
        "dominant_state": dominant_state,
        "dominant_transition_class": dominant_transition_class,
        "drift_class": drift_class,
        "continuity_class": continuity_class,
        "regime_persistence_class": regime_class,
        "triggering_factors": triggering_factors,
        "triggering_factor_count": len(triggering_factors),
        "severity_path": severity_path,
        "transition_class_path": transition_class_path,
        "evidence_summary": evidence_summary,
        "deterministic_attribution_summary": (
            f"{anomaly_class}|states={len(state_path)}|transitions={len(transition_path)}|rule={decision_rule}"
        ),
        "fixed_template_explanation": explanation,
        "precedence_metadata": {
            "ordering": list(ANOMALY_PRECEDENCE),
            "applied_rule": decision_rule,
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
    result["strategic_anomaly_attribution_checksum"] = stable_checksum(
        {k: result[k] for k in result if k != "strategic_anomaly_attribution_checksum"},
        prefix="tier7f_strategic_anomaly_attribution",
    )
    return result


__all__ = [
    "ANOMALY_ATTRIBUTION_CLASSES",
    "ANOMALY_PRECEDENCE",
    "attribute_strategic_anomaly",
]
