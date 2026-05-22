"""Tier 7D deterministic strategic continuity intelligence."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Mapping, Tuple

from transmission_layers.operationalization.serialization import stable_checksum
from .strategic_drift_diagnostics import DRIFT_CLASSES
from .strategic_graph_state import STRATEGIC_STATES
from .strategic_state_transition import SEVERITY_RANKS, TRANSITION_CLASSES

CONTINUITY_CLASSES: Tuple[str, ...] = (
    "continuous",
    "weakly_continuous",
    "interrupted",
    "degrading_continuity",
    "recovering_continuity",
    "oscillating_continuity",
    "blocked_continuity",
    "insufficient_history",
    "invalid_continuity_input",
)

CONTINUITY_PRECEDENCE_ORDER: Tuple[str, ...] = (
    "invalid_continuity_input",
    "insufficient_history",
    "blocked_continuity",
    "oscillating_continuity",
    "degrading_continuity",
    "recovering_continuity",
    "interrupted",
    "weakly_continuous",
    "continuous",
)

_IMPROVING_TRANSITIONS = {"improved", "recovering"}
_WORSENING_TRANSITIONS = {"deteriorated", "destabilized"}


def _extract_state(item: Any) -> str | None:
    if isinstance(item, Mapping):
        value = item.get("strategic_graph_state")
        if isinstance(value, str):
            return value
    if isinstance(item, str):
        return item
    return None


def _extract_transition(item: Any) -> str | None:
    if isinstance(item, Mapping):
        value = item.get("transition_class")
        if isinstance(value, str):
            return value
    if isinstance(item, str):
        return item
    return None


def _extract_drift(item: Any) -> str | None:
    if isinstance(item, Mapping):
        value = item.get("drift_class")
        if isinstance(value, str):
            return value
    if isinstance(item, str):
        return item
    return None


def assess_strategic_continuity(
    strategic_state_sequence: Any,
    transition_sequence: Any | None = None,
    drift_diagnostics: Any | None = None,
) -> Dict[str, Any]:
    states_safe = deepcopy(strategic_state_sequence)
    transitions_safe = deepcopy(transition_sequence) if transition_sequence is not None else []
    drift_safe = deepcopy(drift_diagnostics)

    malformed_input = not isinstance(states_safe, list) or (
        transition_sequence is not None and not isinstance(transitions_safe, list)
    )

    state_path: List[str | None] = []
    transition_path: List[str | None] = []
    drift_class = _extract_drift(drift_safe)

    invalid_state_count = 0
    invalid_transition_count = 0
    invalid_drift_count = 0

    if isinstance(states_safe, list):
        state_path = [_extract_state(item) for item in states_safe]
        invalid_state_count = sum(1 for s in state_path if s not in STRATEGIC_STATES)

    if isinstance(transitions_safe, list):
        transition_path = [_extract_transition(item) for item in transitions_safe]
        invalid_transition_count = sum(1 for t in transition_path if t not in TRANSITION_CLASSES)

    if drift_safe is not None and drift_class not in DRIFT_CLASSES:
        invalid_drift_count = 1

    severity_path = [SEVERITY_RANKS[s] for s in state_path if s in SEVERITY_RANKS]
    deltas = [b - a for a, b in zip(severity_path, severity_path[1:])]
    directions = [1 if d > 0 else -1 if d < 0 else 0 for d in deltas]
    nonzero_directions = [d for d in directions if d != 0]
    direction_change_count = sum(
        1 for i in range(1, len(nonzero_directions)) if nonzero_directions[i] != nonzero_directions[i - 1]
    )

    max_severity_jump = max((abs(d) for d in deltas), default=0)
    worsening_count = sum(1 for t in transition_path if t in _WORSENING_TRANSITIONS)
    improving_count = sum(1 for t in transition_path if t in _IMPROVING_TRANSITIONS)
    non_unchanged_count = sum(1 for t in transition_path if t not in (None, "unchanged"))
    bridge_gap = len(transition_path) not in (0, max(0, len(state_path) - 1))

    initial_state = state_path[0] if state_path else None
    latest_state = state_path[-1] if state_path else None
    initial_rank = SEVERITY_RANKS.get(initial_state, -1)
    latest_rank = SEVERITY_RANKS.get(latest_state, -1)
    net_delta = (latest_rank - initial_rank) if (initial_rank >= 0 and latest_rank >= 0) else 0
    latest_transition = transition_path[-1] if transition_path else None

    if malformed_input:
        continuity_class = "invalid_continuity_input"
        decision_rule = "rule_1_malformed_non_list_state_input"
    elif invalid_state_count > 0 or invalid_transition_count > 0 or invalid_drift_count > 0:
        continuity_class = "invalid_continuity_input"
        decision_rule = "rule_2_invalid_state_transition_or_drift"
    elif len(state_path) < 2:
        continuity_class = "insufficient_history"
        decision_rule = "rule_3_fewer_than_two_states"
    elif latest_state == "structurally_blocked" or latest_transition == "blocked" or drift_class == "blocked":
        continuity_class = "blocked_continuity"
        decision_rule = "rule_4_blocked_latest_state_or_transition_or_drift"
    elif drift_class == "oscillating" or direction_change_count >= 2:
        continuity_class = "oscillating_continuity"
        decision_rule = "rule_5_oscillation_detected"
    elif drift_class == "deteriorating" or worsening_count > (len(transition_path) / 2.0):
        continuity_class = "degrading_continuity"
        decision_rule = "rule_6_deteriorating_or_worsening_majority"
    elif drift_class == "recovering" or improving_count > (len(transition_path) / 2.0):
        continuity_class = "recovering_continuity"
        decision_rule = "rule_7_recovering_or_improving_majority"
    elif bridge_gap or max_severity_jump >= 3:
        continuity_class = "interrupted"
        decision_rule = "rule_8_missing_bridge_or_severity_jump"
    elif any(delta != 0 for delta in deltas) or non_unchanged_count > 0:
        continuity_class = "weakly_continuous"
        decision_rule = "rule_9_nonzero_movement_or_non_unchanged_transition"
    else:
        continuity_class = "continuous"
        decision_rule = "rule_10_default_continuous"

    evidence_summary = {
        "malformed_input": malformed_input,
        "invalid_state_count": invalid_state_count,
        "invalid_transition_count": invalid_transition_count,
        "invalid_drift_count": invalid_drift_count,
        "latest_transition_class": latest_transition,
        "worsening_transition_count": worsening_count,
        "improving_transition_count": improving_count,
        "non_unchanged_transition_count": non_unchanged_count,
        "bridge_gap_detected": bridge_gap,
        "decision_rule": decision_rule,
    }

    explanation = (
        "Strategic continuity intelligence is deterministic: "
        f"continuity_class={continuity_class}; state_count={len(state_path)}; transition_count={len(transition_path)}; "
        f"initial_state={initial_state}; latest_state={latest_state}; net_severity_delta={net_delta}; "
        f"max_severity_jump={max_severity_jump}; direction_change_count={direction_change_count}; rule={decision_rule}."
    )

    result = {
        "continuity_class": continuity_class,
        "state_count": len(state_path),
        "transition_count": len(transition_path),
        "initial_state": initial_state,
        "latest_state": latest_state,
        "initial_severity_rank": initial_rank,
        "latest_severity_rank": latest_rank,
        "net_severity_delta": net_delta,
        "max_severity_jump": max_severity_jump,
        "severity_path": severity_path,
        "transition_class_path": [t for t in transition_path if isinstance(t, str)],
        "drift_class": drift_class,
        "direction_change_count": direction_change_count,
        "deterministic_evidence_summary": evidence_summary,
        "explanation": explanation,
        "precedence_ordering": list(CONTINUITY_PRECEDENCE_ORDER),
        "severity_rank_ordering": dict(SEVERITY_RANKS),
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
    result["strategic_continuity_checksum"] = stable_checksum(
        {
            "continuity_class": result["continuity_class"],
            "state_count": result["state_count"],
            "transition_count": result["transition_count"],
            "initial_state": result["initial_state"],
            "latest_state": result["latest_state"],
            "initial_severity_rank": result["initial_severity_rank"],
            "latest_severity_rank": result["latest_severity_rank"],
            "net_severity_delta": result["net_severity_delta"],
            "max_severity_jump": result["max_severity_jump"],
            "severity_path": result["severity_path"],
            "transition_class_path": result["transition_class_path"],
            "drift_class": result["drift_class"],
            "direction_change_count": result["direction_change_count"],
            "deterministic_evidence_summary": result["deterministic_evidence_summary"],
            "precedence_ordering": result["precedence_ordering"],
            "severity_rank_ordering": result["severity_rank_ordering"],
            "invariant_flags": result["invariant_flags"],
        },
        prefix="tier7d_strategic_continuity",
    )
    return result


__all__ = [
    "CONTINUITY_CLASSES",
    "CONTINUITY_PRECEDENCE_ORDER",
    "assess_strategic_continuity",
]
