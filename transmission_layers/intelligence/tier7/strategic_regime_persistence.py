"""Tier 7E deterministic strategic regime persistence intelligence."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Mapping, Tuple

from transmission_layers.operationalization.serialization import stable_checksum
from .strategic_continuity import CONTINUITY_CLASSES
from .strategic_drift_diagnostics import DRIFT_CLASSES
from .strategic_graph_state import STRATEGIC_STATES
from .strategic_state_transition import SEVERITY_RANKS, TRANSITION_CLASSES

REGIME_PERSISTENCE_CLASSES: Tuple[str, ...] = (
    "persistent_regime",
    "weakly_persistent_regime",
    "unstable_regime",
    "shifting_regime",
    "degrading_regime",
    "recovering_regime",
    "blocked_regime",
    "insufficient_history",
    "invalid_regime_input",
)

REGIME_BAND_ORDERING: Dict[str, Tuple[str, ...]] = {
    "stable_band": ("stable", "stressed"),
    "transition_band": ("transitional", "regime_shifting"),
    "distortion_band": ("distorted", "fragmented"),
    "fragility_band": ("fragile", "degraded"),
    "blocked_band": ("structurally_blocked",),
}

REGIME_PERSISTENCE_PRECEDENCE: Tuple[str, ...] = (
    "rule_1_malformed_non_list_state_input",
    "rule_2_invalid_state_transition_drift_or_continuity",
    "rule_3_fewer_than_three_states",
    "rule_4_blocked_condition",
    "rule_5_degrading_condition",
    "rule_6_recovering_condition",
    "rule_7_shifting_condition",
    "rule_8_unstable_condition",
    "rule_9_weakly_persistent_condition",
    "rule_10_default_persistent",
)

_WORSENING_TRANSITIONS = {"deteriorated", "destabilized"}
_IMPROVING_TRANSITIONS = {"improved", "recovering"}


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


def _band_for_state(state: str | None) -> str:
    for band, labels in REGIME_BAND_ORDERING.items():
        if state in labels:
            return band
    return "invalid_band"


def assess_strategic_regime_persistence(
    strategic_state_sequence: Any,
    transition_sequence: Any | None = None,
    drift_diagnostics: Any | None = None,
    continuity_assessment: Any | None = None,
) -> Dict[str, Any]:
    states_safe = deepcopy(strategic_state_sequence)
    transitions_safe = deepcopy(transition_sequence) if transition_sequence is not None else []
    drift_safe = deepcopy(drift_diagnostics)
    continuity_safe = deepcopy(continuity_assessment)

    malformed_input = not isinstance(states_safe, list) or (
        transition_sequence is not None and not isinstance(transitions_safe, list)
    )

    state_path: List[str | None] = []
    transition_path: List[str | None] = []
    drift_class = _extract_drift(drift_safe)
    continuity_class = _extract_continuity(continuity_safe)

    if isinstance(states_safe, list):
        state_path = [_extract_state(item) for item in states_safe]
    if isinstance(transitions_safe, list):
        transition_path = [_extract_transition(item) for item in transitions_safe]

    invalid_state_count = sum(1 for s in state_path if s not in STRATEGIC_STATES)
    invalid_transition_count = sum(1 for t in transition_path if t not in TRANSITION_CLASSES)
    invalid_drift_count = 0 if drift_safe is None or drift_class in DRIFT_CLASSES else 1
    invalid_continuity_count = 0 if continuity_safe is None or continuity_class in CONTINUITY_CLASSES else 1

    severity_path = [SEVERITY_RANKS[s] for s in state_path if s in SEVERITY_RANKS]
    deltas = [b - a for a, b in zip(severity_path, severity_path[1:])]
    max_severity_jump = max((abs(d) for d in deltas), default=0)
    nonzero_directions = [1 if d > 0 else -1 for d in deltas if d != 0]
    direction_change_count = sum(
        1 for i in range(1, len(nonzero_directions)) if nonzero_directions[i] != nonzero_directions[i - 1]
    )

    regime_band_path = [_band_for_state(s) for s in state_path if isinstance(s, str)]
    mixed_regime_band_count = len(set(regime_band_path)) if regime_band_path else 0

    initial_state = state_path[0] if state_path else None
    latest_state = state_path[-1] if state_path else None
    initial_rank = SEVERITY_RANKS.get(initial_state, -1)
    latest_rank = SEVERITY_RANKS.get(latest_state, -1)
    net_delta = (latest_rank - initial_rank) if initial_rank >= 0 and latest_rank >= 0 else 0

    counts: Dict[str, int] = {}
    for s in state_path:
        if isinstance(s, str):
            counts[s] = counts.get(s, 0) + 1
    dominant_state = sorted(counts.items(), key=lambda x: (-x[1], SEVERITY_RANKS.get(x[0], 99), x[0]))[0][0] if counts else None
    dominant_regime_band = _band_for_state(dominant_state)

    worsening_count = sum(1 for t in transition_path if t in _WORSENING_TRANSITIONS)
    improving_count = sum(1 for t in transition_path if t in _IMPROVING_TRANSITIONS)
    latest_transition = transition_path[-1] if transition_path else None

    if malformed_input:
        regime_class = "invalid_regime_input"
        decision_rule = REGIME_PERSISTENCE_PRECEDENCE[0]
    elif invalid_state_count > 0 or invalid_transition_count > 0 or invalid_drift_count > 0 or invalid_continuity_count > 0:
        regime_class = "invalid_regime_input"
        decision_rule = REGIME_PERSISTENCE_PRECEDENCE[1]
    elif len(state_path) < 3:
        regime_class = "insufficient_history"
        decision_rule = REGIME_PERSISTENCE_PRECEDENCE[2]
    elif latest_state == "structurally_blocked" or latest_transition == "blocked" or drift_class == "blocked" or continuity_class == "blocked_continuity":
        regime_class = "blocked_regime"
        decision_rule = REGIME_PERSISTENCE_PRECEDENCE[3]
    elif drift_class == "deteriorating" or continuity_class == "degrading_continuity" or worsening_count > (len(transition_path) / 2.0):
        regime_class = "degrading_regime"
        decision_rule = REGIME_PERSISTENCE_PRECEDENCE[4]
    elif drift_class == "recovering" or continuity_class == "recovering_continuity" or improving_count > (len(transition_path) / 2.0):
        regime_class = "recovering_regime"
        decision_rule = REGIME_PERSISTENCE_PRECEDENCE[5]
    elif latest_state == "regime_shifting" or drift_class in {"drifting", "oscillating"} or continuity_class == "oscillating_continuity" or direction_change_count >= 2:
        regime_class = "shifting_regime"
        decision_rule = REGIME_PERSISTENCE_PRECEDENCE[6]
    elif max_severity_jump >= 3 or continuity_class == "interrupted" or mixed_regime_band_count >= 3:
        regime_class = "unstable_regime"
        decision_rule = REGIME_PERSISTENCE_PRECEDENCE[7]
    elif any(d != 0 for d in deltas) or continuity_class == "weakly_continuous":
        regime_class = "weakly_persistent_regime"
        decision_rule = REGIME_PERSISTENCE_PRECEDENCE[8]
    else:
        regime_class = "persistent_regime"
        decision_rule = REGIME_PERSISTENCE_PRECEDENCE[9]

    evidence = {
        "malformed_input": malformed_input,
        "invalid_state_count": invalid_state_count,
        "invalid_transition_count": invalid_transition_count,
        "invalid_drift_count": invalid_drift_count,
        "invalid_continuity_count": invalid_continuity_count,
        "worsening_transition_count": worsening_count,
        "improving_transition_count": improving_count,
        "latest_transition_class": latest_transition,
        "decision_rule": decision_rule,
    }

    result = {
        "regime_persistence_class": regime_class,
        "state_count": len(state_path),
        "transition_count": len(transition_path),
        "initial_state": initial_state,
        "latest_state": latest_state,
        "dominant_state": dominant_state,
        "dominant_regime_band": dominant_regime_band,
        "initial_severity_rank": initial_rank,
        "latest_severity_rank": latest_rank,
        "net_severity_delta": net_delta,
        "max_severity_jump": max_severity_jump,
        "severity_path": severity_path,
        "transition_class_path": [t for t in transition_path if isinstance(t, str)],
        "drift_class": drift_class,
        "continuity_class": continuity_class,
        "direction_change_count": direction_change_count,
        "regime_band_path": regime_band_path,
        "mixed_regime_band_count": mixed_regime_band_count,
        "deterministic_evidence_summary": evidence,
        "explanation": (
            "Strategic regime persistence intelligence is deterministic: "
            f"regime_persistence_class={regime_class}; state_count={len(state_path)}; transition_count={len(transition_path)}; "
            f"initial_state={initial_state}; latest_state={latest_state}; net_severity_delta={net_delta}; "
            f"max_severity_jump={max_severity_jump}; direction_change_count={direction_change_count}; rule={decision_rule}."
        ),
        "precedence_ordering": list(REGIME_PERSISTENCE_PRECEDENCE),
        "severity_rank_ordering": dict(SEVERITY_RANKS),
        "regime_band_ordering": {k: list(v) for k, v in REGIME_BAND_ORDERING.items()},
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
    result["strategic_regime_persistence_checksum"] = stable_checksum(
        {k: result[k] for k in result if k != "strategic_regime_persistence_checksum"},
        prefix="tier7e_strategic_regime_persistence",
    )
    return result


__all__ = [
    "REGIME_PERSISTENCE_CLASSES",
    "REGIME_BAND_ORDERING",
    "REGIME_PERSISTENCE_PRECEDENCE",
    "assess_strategic_regime_persistence",
]
