"""Tier 7B deterministic strategic state transition intelligence."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Mapping, Tuple

from transmission_layers.operationalization.serialization import stable_checksum
from .strategic_graph_state import STRATEGIC_STATES

TRANSITION_CLASSES: Tuple[str, ...] = (
    "unchanged",
    "improved",
    "deteriorated",
    "destabilized",
    "recovering",
    "blocked",
    "invalid_transition",
)

SEVERITY_RANKS: Dict[str, int] = {
    "stable": 0,
    "stressed": 1,
    "transitional": 2,
    "regime_shifting": 3,
    "distorted": 4,
    "fragmented": 5,
    "fragile": 6,
    "degraded": 7,
    "structurally_blocked": 8,
    "invalid_input": 9,
}

TRANSITION_PRECEDENCE: Tuple[str, ...] = (
    "invalid_transition",
    "blocked",
    "recovering",
    "unchanged",
    "destabilized",
    "deteriorated",
    "improved",
)


def _extract_state(payload: Any) -> str | None:
    if isinstance(payload, Mapping):
        value = payload.get("strategic_graph_state")
        if isinstance(value, str):
            return value
    if isinstance(payload, str):
        return payload
    return None


def assess_strategic_state_transition(previous_state: Any, current_state: Any) -> Dict[str, Any]:
    previous_safe = deepcopy(previous_state)
    current_safe = deepcopy(current_state)

    prev_label = _extract_state(previous_safe)
    curr_label = _extract_state(current_safe)

    malformed = prev_label is None or curr_label is None
    prev_valid = isinstance(prev_label, str) and prev_label in STRATEGIC_STATES
    curr_valid = isinstance(curr_label, str) and curr_label in STRATEGIC_STATES

    if malformed or not prev_valid or not curr_valid or prev_label == "invalid_input" or curr_label == "invalid_input":
        transition_class = "invalid_transition"
    elif curr_label == "structurally_blocked":
        transition_class = "blocked"
    elif prev_label == "structurally_blocked" and curr_label != "structurally_blocked":
        transition_class = "recovering"
    elif prev_label == curr_label:
        transition_class = "unchanged"
    else:
        delta = SEVERITY_RANKS[curr_label] - SEVERITY_RANKS[prev_label]
        if delta >= 3:
            transition_class = "destabilized"
        elif delta >= 1:
            transition_class = "deteriorated"
        elif delta < 0:
            transition_class = "improved"
        else:
            transition_class = "unchanged"

    prev_rank = SEVERITY_RANKS.get(prev_label, -1)
    curr_rank = SEVERITY_RANKS.get(curr_label, -1)
    delta = curr_rank - prev_rank

    evidence_summary = {
        "previous_state_valid": prev_valid,
        "current_state_valid": curr_valid,
        "malformed_input": malformed,
        "previous_is_blocked": prev_label == "structurally_blocked",
        "current_is_blocked": curr_label == "structurally_blocked",
        "previous_is_invalid_input": prev_label == "invalid_input",
        "current_is_invalid_input": curr_label == "invalid_input",
    }

    explanation = (
        "Strategic state transition intelligence is deterministic: "
        f"previous={prev_label}; current={curr_label}; class={transition_class}; "
        f"previous_rank={prev_rank}; current_rank={curr_rank}; severity_delta={delta}."
    )

    result = {
        "previous_strategic_graph_state": prev_label,
        "current_strategic_graph_state": curr_label,
        "transition_class": transition_class,
        "previous_severity_rank": prev_rank,
        "current_severity_rank": curr_rank,
        "severity_delta": delta,
        "deterministic_transition_evidence_summary": evidence_summary,
        "explanation": explanation,
        "transition_class_ordering": list(TRANSITION_PRECEDENCE),
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
    result["strategic_state_transition_checksum"] = stable_checksum(
        {
            "previous_strategic_graph_state": result["previous_strategic_graph_state"],
            "current_strategic_graph_state": result["current_strategic_graph_state"],
            "transition_class": result["transition_class"],
            "previous_severity_rank": result["previous_severity_rank"],
            "current_severity_rank": result["current_severity_rank"],
            "severity_delta": result["severity_delta"],
            "deterministic_transition_evidence_summary": result["deterministic_transition_evidence_summary"],
            "invariant_flags": result["invariant_flags"],
        },
        prefix="tier7b_strategic_transition",
    )
    return result


__all__ = [
    "TRANSITION_CLASSES",
    "SEVERITY_RANKS",
    "TRANSITION_PRECEDENCE",
    "assess_strategic_state_transition",
]
