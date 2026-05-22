"""Tier 7I deterministic strategic causality replay intelligence."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Mapping, Tuple

from transmission_layers.operationalization.serialization import stable_checksum
from .strategic_anomaly_attribution import ANOMALY_ATTRIBUTION_CLASSES
from .strategic_coherence import COHERENCE_CLASSES
from .strategic_continuity import CONTINUITY_CLASSES
from .strategic_drift_diagnostics import DRIFT_CLASSES
from .strategic_graph_state import STRATEGIC_STATES
from .strategic_regime_persistence import REGIME_PERSISTENCE_CLASSES
from .strategic_stability_resilience import STABILITY_RESILIENCE_CLASSES
from .strategic_state_transition import SEVERITY_RANKS, TRANSITION_CLASSES

CAUSALITY_REPLAY_CLASSES: Tuple[str, ...] = (
    "no_causal_change",
    "weak_causal_chain",
    "coherent_causal_chain",
    "degraded_causal_chain",
    "fragmented_causal_chain",
    "blocked_causal_chain",
    "incoherent_causal_chain",
    "insufficient_replay_history",
    "invalid_causality_replay_input",
)

CAUSALITY_REPLAY_PRECEDENCE: Tuple[str, ...] = (
    "rule_1_malformed_non_list_state_input",
    "rule_2_invalid_state_or_transition_or_drift_or_continuity_or_regime_or_anomaly_or_coherence_or_stability",
    "rule_3_fewer_than_two_states",
    "rule_4_blocked_condition",
    "rule_5_incoherent_condition",
    "rule_6_fragmented_condition",
    "rule_7_degraded_condition",
    "rule_8_coherent_nonzero_movement",
    "rule_9_weak_nonzero_movement",
    "rule_10_default_no_causal_change",
)

_ALLOWED_STEP_LABELS: Tuple[str, ...] = (
    "stable_persistence",
    "stress_accumulation",
    "strategic_transition",
    "regime_shift_progression",
    "distortion_propagation",
    "fragmentation_propagation",
    "fragility_escalation",
    "degradation_escalation",
    "blocked_propagation",
    "recovery_path",
    "invalid_replay_step",
)


def _extract(payload: Any, key: str) -> str | None:
    if isinstance(payload, Mapping):
        value = payload.get(key)
        return value if isinstance(value, str) else None
    return payload if isinstance(payload, str) else None


def _label_for_step(current_state: str | None, severity_delta: int, transition_class: str | None) -> str:
    if current_state == "structurally_blocked" or transition_class == "blocked":
        return "blocked_propagation"
    if current_state == "degraded":
        return "degradation_escalation"
    if current_state == "fragmented":
        return "fragmentation_propagation"
    if current_state == "distorted":
        return "distortion_propagation"
    if current_state == "fragile":
        return "fragility_escalation"
    if current_state == "regime_shifting":
        return "regime_shift_progression"
    if severity_delta > 0:
        return "stress_accumulation"
    if severity_delta < 0:
        return "recovery_path"
    if current_state == "transitional":
        return "strategic_transition"
    return "stable_persistence"


def replay_strategic_causality(
    strategic_state_sequence: Any,
    transition_sequence: Any | None = None,
    drift_diagnostics: Any | None = None,
    continuity_assessment: Any | None = None,
    regime_persistence_assessment: Any | None = None,
    anomaly_attribution: Any | None = None,
    coherence_assessment: Any | None = None,
    stability_resilience_assessment: Any | None = None,
    structural_evidence_sequence: Any | None = None,
) -> Dict[str, Any]:
    states_safe = deepcopy(strategic_state_sequence)
    transitions_safe = deepcopy(transition_sequence) if transition_sequence is not None else []
    drift_safe = deepcopy(drift_diagnostics)
    continuity_safe = deepcopy(continuity_assessment)
    regime_safe = deepcopy(regime_persistence_assessment)
    anomaly_safe = deepcopy(anomaly_attribution)
    coherence_safe = deepcopy(coherence_assessment)
    stability_safe = deepcopy(stability_resilience_assessment)
    evidence_safe = deepcopy(structural_evidence_sequence) if structural_evidence_sequence is not None else []

    malformed_input = not isinstance(states_safe, list) or (transition_sequence is not None and not isinstance(transitions_safe, list))
    malformed_evidence = structural_evidence_sequence is not None and not isinstance(evidence_safe, list)

    state_path: List[str | None] = [_extract(s, "strategic_graph_state") for s in states_safe] if isinstance(states_safe, list) else []
    transition_path_raw: List[str | None] = [_extract(t, "transition_class") for t in transitions_safe] if isinstance(transitions_safe, list) else []

    drift_class = _extract(drift_safe, "drift_class")
    continuity_class = _extract(continuity_safe, "continuity_class")
    regime_class = _extract(regime_safe, "regime_persistence_class")
    anomaly_class = _extract(anomaly_safe, "anomaly_attribution_class")
    coherence_class = _extract(coherence_safe, "coherence_class")
    stability_class = _extract(stability_safe, "stability_resilience_class")

    invalid_state_count = sum(1 for s in state_path if s not in STRATEGIC_STATES)
    invalid_transition_count = sum(1 for t in transition_path_raw if t not in TRANSITION_CLASSES)
    invalid_drift_count = 0 if drift_safe is None or drift_class in DRIFT_CLASSES else 1
    invalid_continuity_count = 0 if continuity_safe is None or continuity_class in CONTINUITY_CLASSES else 1
    invalid_regime_count = 0 if regime_safe is None or regime_class in REGIME_PERSISTENCE_CLASSES else 1
    invalid_anomaly_count = 0 if anomaly_safe is None or anomaly_class in ANOMALY_ATTRIBUTION_CLASSES else 1
    invalid_coherence_count = 0 if coherence_safe is None or coherence_class in COHERENCE_CLASSES else 1
    invalid_stability_count = 0 if stability_safe is None or stability_class in STABILITY_RESILIENCE_CLASSES else 1
    invalid_evidence_count = 0 if isinstance(evidence_safe, list) else 1
    if isinstance(evidence_safe, list):
        invalid_evidence_count += sum(1 for item in evidence_safe if not isinstance(item, dict))

    severity_path = [SEVERITY_RANKS[s] for s in state_path if s in SEVERITY_RANKS]
    deltas = [b - a for a, b in zip(severity_path, severity_path[1:])]

    initial_state = state_path[0] if state_path else None
    latest_state = state_path[-1] if state_path else None
    initial_rank = SEVERITY_RANKS.get(initial_state, -1)
    latest_rank = SEVERITY_RANKS.get(latest_state, -1)
    net_delta = (latest_rank - initial_rank) if (initial_rank >= 0 and latest_rank >= 0) else 0
    max_jump = max((abs(d) for d in deltas), default=0)

    transition_class_path = [t for t in transition_path_raw if isinstance(t, str)]
    latest_transition = transition_class_path[-1] if transition_class_path else None

    blocked_condition = (
        latest_state == "structurally_blocked"
        or latest_transition == "blocked"
        or drift_class == "blocked"
        or continuity_class == "blocked_continuity"
        or regime_class == "blocked_regime"
        or anomaly_class == "blocked_anomaly"
        or stability_class == "blocked"
    )
    incoherent_condition = coherence_class in {"contradictory", "incoherent"} or stability_class == "incoherent"
    fragmented_condition = latest_state == "fragmented" or anomaly_class == "fragmentation_anomaly"
    degraded_condition = (
        latest_state == "degraded"
        or drift_class == "deteriorating"
        or regime_class == "degrading_regime"
        or anomaly_class == "degradation_anomaly"
        or stability_class == "degraded"
    )
    coherent_context = coherence_class in {"coherent", "weakly_coherent"}

    if malformed_input or malformed_evidence:
        replay_class, rule = "invalid_causality_replay_input", CAUSALITY_REPLAY_PRECEDENCE[0]
    elif any((
        invalid_state_count > 0,
        invalid_transition_count > 0,
        invalid_drift_count > 0,
        invalid_continuity_count > 0,
        invalid_regime_count > 0,
        invalid_anomaly_count > 0,
        invalid_coherence_count > 0,
        invalid_stability_count > 0,
        invalid_evidence_count > 0,
    )):
        replay_class, rule = "invalid_causality_replay_input", CAUSALITY_REPLAY_PRECEDENCE[1]
    elif len(state_path) < 2:
        replay_class, rule = "insufficient_replay_history", CAUSALITY_REPLAY_PRECEDENCE[2]
    elif blocked_condition:
        replay_class, rule = "blocked_causal_chain", CAUSALITY_REPLAY_PRECEDENCE[3]
    elif incoherent_condition:
        replay_class, rule = "incoherent_causal_chain", CAUSALITY_REPLAY_PRECEDENCE[4]
    elif fragmented_condition:
        replay_class, rule = "fragmented_causal_chain", CAUSALITY_REPLAY_PRECEDENCE[5]
    elif degraded_condition:
        replay_class, rule = "degraded_causal_chain", CAUSALITY_REPLAY_PRECEDENCE[6]
    elif net_delta != 0 and coherent_context:
        replay_class, rule = "coherent_causal_chain", CAUSALITY_REPLAY_PRECEDENCE[7]
    elif net_delta != 0:
        replay_class, rule = "weak_causal_chain", CAUSALITY_REPLAY_PRECEDENCE[8]
    else:
        replay_class, rule = "no_causal_change", CAUSALITY_REPLAY_PRECEDENCE[9]

    causal_replay_steps: List[Dict[str, Any]] = []
    for idx in range(1, len(state_path)):
        prev_state = state_path[idx - 1]
        cur_state = state_path[idx]
        prev_rank = SEVERITY_RANKS.get(prev_state, -1)
        cur_rank = SEVERITY_RANKS.get(cur_state, -1)
        severity_delta = cur_rank - prev_rank if (prev_rank >= 0 and cur_rank >= 0) else 0
        transition_class = transition_class_path[idx - 1] if idx - 1 < len(transition_class_path) else None
        if severity_delta > 0:
            direction = "deteriorating"
        elif severity_delta < 0:
            direction = "improving"
        else:
            direction = "unchanged"
        label = _label_for_step(cur_state, severity_delta, transition_class)
        causal_replay_steps.append(
            {
                "step_index": idx,
                "previous_state": prev_state,
                "current_state": cur_state,
                "previous_severity_rank": prev_rank,
                "current_severity_rank": cur_rank,
                "severity_delta": severity_delta,
                "transition_class": transition_class,
                "causal_direction": direction,
                "bounded_causal_label": label if label in _ALLOWED_STEP_LABELS else "invalid_replay_step",
            }
        )

    causal_factor_path = [
        factor
        for factor, ok in (
            ("blocked_condition", blocked_condition),
            ("incoherent_condition", incoherent_condition),
            ("fragmented_condition", fragmented_condition),
            ("degraded_condition", degraded_condition),
            ("coherent_context", coherent_context),
            ("net_severity_movement", net_delta != 0),
            ("insufficient_history", len(state_path) < 2),
        )
        if ok
    ]

    evidence_summary = {
        "malformed_input": malformed_input,
        "malformed_evidence": malformed_evidence,
        "invalid_state_count": invalid_state_count,
        "invalid_transition_count": invalid_transition_count,
        "invalid_drift_count": invalid_drift_count,
        "invalid_continuity_count": invalid_continuity_count,
        "invalid_regime_count": invalid_regime_count,
        "invalid_anomaly_count": invalid_anomaly_count,
        "invalid_coherence_count": invalid_coherence_count,
        "invalid_stability_count": invalid_stability_count,
        "invalid_evidence_count": invalid_evidence_count,
        "latest_transition_class": latest_transition,
        "structural_evidence_keys_path": [sorted(str(k) for k in d.keys()) for d in evidence_safe] if isinstance(evidence_safe, list) else [],
        "decision_rule": rule,
    }

    result = {
        "causality_replay_class": replay_class,
        "state_count": len(state_path),
        "transition_count": len(transition_class_path),
        "evidence_count": len(evidence_safe) if isinstance(evidence_safe, list) else 0,
        "initial_state": initial_state,
        "latest_state": latest_state,
        "initial_severity_rank": initial_rank,
        "latest_severity_rank": latest_rank,
        "net_severity_delta": net_delta,
        "max_severity_jump": max_jump,
        "severity_path": severity_path,
        "transition_class_path": transition_class_path,
        "drift_class": drift_class,
        "continuity_class": continuity_class,
        "regime_persistence_class": regime_class,
        "anomaly_attribution_class": anomaly_class,
        "coherence_class": coherence_class,
        "stability_resilience_class": stability_class,
        "causal_replay_steps": causal_replay_steps,
        "causal_factor_path": causal_factor_path,
        "causal_factor_count": len(causal_factor_path),
        "deterministic_evidence_summary": evidence_summary,
        "fixed_template_explanation": (
            "Strategic causality replay intelligence is deterministic: "
            f"causality_replay_class={replay_class}; state_count={len(state_path)}; transition_count={len(transition_class_path)}; "
            f"initial_state={initial_state}; latest_state={latest_state}; net_severity_delta={net_delta}; "
            f"max_severity_jump={max_jump}; drift_class={drift_class}; continuity_class={continuity_class}; "
            f"regime_persistence_class={regime_class}; anomaly_attribution_class={anomaly_class}; coherence_class={coherence_class}; "
            f"stability_resilience_class={stability_class}; rule={rule}."
        ),
        "precedence_metadata": {
            "ordering": list(CAUSALITY_REPLAY_PRECEDENCE),
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
    result["strategic_causality_replay_checksum"] = stable_checksum(
        {k: result[k] for k in result if k != "strategic_causality_replay_checksum"},
        prefix="tier7i_strategic_causality_replay",
    )
    return result


__all__ = [
    "CAUSALITY_REPLAY_CLASSES",
    "CAUSALITY_REPLAY_PRECEDENCE",
    "replay_strategic_causality",
]
