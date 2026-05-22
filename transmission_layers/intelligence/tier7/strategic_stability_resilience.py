"""Tier 7H deterministic strategic stability and resilience intelligence."""
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
from .strategic_state_transition import SEVERITY_RANKS, TRANSITION_CLASSES

STABILITY_RESILIENCE_CLASSES: Tuple[str, ...] = (
    "resilient",
    "stable",
    "weakly_stable",
    "fragile",
    "degraded",
    "blocked",
    "incoherent",
    "insufficient_history",
    "invalid_stability_input",
)

STABILITY_RESILIENCE_PRECEDENCE: Tuple[str, ...] = (
    "rule_1_malformed_non_list_state_input",
    "rule_2_invalid_state_or_transition_or_drift_or_continuity_or_regime_or_anomaly_or_coherence",
    "rule_3_fewer_than_three_states",
    "rule_4_blocked_condition",
    "rule_5_incoherent_condition",
    "rule_6_degraded_condition",
    "rule_7_fragile_condition",
    "rule_8_weakly_stable_condition",
    "rule_9_resilient_condition",
    "rule_10_default_stable",
)


def _extract(payload: Any, key: str) -> str | None:
    if isinstance(payload, Mapping):
        value = payload.get(key)
        return value if isinstance(value, str) else None
    return payload if isinstance(payload, str) else None


def assess_strategic_stability_resilience(
    strategic_state_sequence: Any,
    transition_sequence: Any | None = None,
    drift_diagnostics: Any | None = None,
    continuity_assessment: Any | None = None,
    regime_persistence_assessment: Any | None = None,
    anomaly_attribution: Any | None = None,
    coherence_assessment: Any | None = None,
    structural_evidence: Any | None = None,
) -> Dict[str, Any]:
    states_safe = deepcopy(strategic_state_sequence)
    transitions_safe = deepcopy(transition_sequence) if transition_sequence is not None else []
    drift_safe = deepcopy(drift_diagnostics)
    continuity_safe = deepcopy(continuity_assessment)
    regime_safe = deepcopy(regime_persistence_assessment)
    anomaly_safe = deepcopy(anomaly_attribution)
    coherence_safe = deepcopy(coherence_assessment)
    evidence_safe = deepcopy(structural_evidence) if isinstance(structural_evidence, dict) else {}

    malformed_input = not isinstance(states_safe, list) or (transition_sequence is not None and not isinstance(transitions_safe, list))

    state_path: List[str | None] = [_extract(s, "strategic_graph_state") for s in states_safe] if isinstance(states_safe, list) else []
    transition_path: List[str | None] = [_extract(t, "transition_class") for t in transitions_safe] if isinstance(transitions_safe, list) else []

    drift_class = _extract(drift_safe, "drift_class")
    continuity_class = _extract(continuity_safe, "continuity_class")
    regime_class = _extract(regime_safe, "regime_persistence_class")
    anomaly_class = _extract(anomaly_safe, "anomaly_attribution_class")
    coherence_class = _extract(coherence_safe, "coherence_class")

    invalid_state_count = sum(1 for s in state_path if s not in STRATEGIC_STATES)
    invalid_transition_count = sum(1 for t in transition_path if t not in TRANSITION_CLASSES)
    invalid_drift_count = 0 if drift_safe is None or drift_class in DRIFT_CLASSES else 1
    invalid_continuity_count = 0 if continuity_safe is None or continuity_class in CONTINUITY_CLASSES else 1
    invalid_regime_count = 0 if regime_safe is None or regime_class in REGIME_PERSISTENCE_CLASSES else 1
    invalid_anomaly_count = 0 if anomaly_safe is None or anomaly_class in ANOMALY_ATTRIBUTION_CLASSES else 1
    invalid_coherence_count = 0 if coherence_safe is None or coherence_class in COHERENCE_CLASSES else 1

    severity_path = [SEVERITY_RANKS[s] for s in state_path if s in SEVERITY_RANKS]
    deltas = [b - a for a, b in zip(severity_path, severity_path[1:])]

    initial_state = state_path[0] if state_path else None
    latest_state = state_path[-1] if state_path else None
    initial_rank = SEVERITY_RANKS.get(initial_state, -1)
    latest_rank = SEVERITY_RANKS.get(latest_state, -1)
    net_delta = (latest_rank - initial_rank) if (initial_rank >= 0 and latest_rank >= 0) else 0
    max_severity_jump = max((abs(d) for d in deltas), default=0)

    state_counts: Dict[str, int] = {}
    for s in state_path:
        if isinstance(s, str):
            state_counts[s] = state_counts.get(s, 0) + 1
    dominant_state = sorted(state_counts.items(), key=lambda x: (-x[1], SEVERITY_RANKS.get(x[0], 99), x[0]))[0][0] if state_counts else None

    latest_transition = transition_path[-1] if transition_path else None

    blocked_condition = (
        latest_state == "structurally_blocked"
        or latest_transition == "blocked"
        or drift_class == "blocked"
        or continuity_class == "blocked_continuity"
        or regime_class == "blocked_regime"
        or anomaly_class == "blocked_anomaly"
    )
    incoherent_condition = coherence_class in {"contradictory", "incoherent", "blocked_coherence"}
    degraded_condition = (
        latest_state == "degraded"
        or drift_class == "deteriorating"
        or continuity_class == "degrading_continuity"
        or regime_class == "degrading_regime"
        or anomaly_class == "degradation_anomaly"
    )
    fragile_condition = (
        latest_state == "fragile"
        or (latest_state in {"fragmented", "distorted"} and anomaly_class in {"fragmentation_anomaly", "distortion_anomaly"})
        or regime_class == "unstable_regime"
        or drift_class == "oscillating"
        or continuity_class == "oscillating_continuity"
    )
    weakly_stable_condition = (
        net_delta > 0
        or continuity_class == "weakly_continuous"
        or regime_class == "weakly_persistent_regime"
        or coherence_class == "weakly_coherent"
        or anomaly_class in {"stress_anomaly", "transition_anomaly"}
    )
    resilient_condition = (
        latest_state == "stable"
        and continuity_class == "continuous"
        and regime_class == "persistent_regime"
        and coherence_class == "coherent"
        and anomaly_class == "no_anomaly"
        and net_delta <= 0
    )

    if malformed_input:
        out_class, rule = "invalid_stability_input", STABILITY_RESILIENCE_PRECEDENCE[0]
    elif any((
        invalid_state_count > 0,
        invalid_transition_count > 0,
        invalid_drift_count > 0,
        invalid_continuity_count > 0,
        invalid_regime_count > 0,
        invalid_anomaly_count > 0,
        invalid_coherence_count > 0,
    )):
        out_class, rule = "invalid_stability_input", STABILITY_RESILIENCE_PRECEDENCE[1]
    elif len(state_path) < 3:
        out_class, rule = "insufficient_history", STABILITY_RESILIENCE_PRECEDENCE[2]
    elif blocked_condition:
        out_class, rule = "blocked", STABILITY_RESILIENCE_PRECEDENCE[3]
    elif incoherent_condition:
        out_class, rule = "incoherent", STABILITY_RESILIENCE_PRECEDENCE[4]
    elif degraded_condition:
        out_class, rule = "degraded", STABILITY_RESILIENCE_PRECEDENCE[5]
    elif fragile_condition:
        out_class, rule = "fragile", STABILITY_RESILIENCE_PRECEDENCE[6]
    elif weakly_stable_condition:
        out_class, rule = "weakly_stable", STABILITY_RESILIENCE_PRECEDENCE[7]
    elif resilient_condition:
        out_class, rule = "resilient", STABILITY_RESILIENCE_PRECEDENCE[8]
    else:
        out_class, rule = "stable", STABILITY_RESILIENCE_PRECEDENCE[9]

    resilience_factors = [
        factor for factor, ok in (
            ("severity_non_increasing", net_delta <= 0),
            ("latest_state_stable", latest_state == "stable"),
            ("continuous_continuity", continuity_class == "continuous"),
            ("persistent_regime", regime_class == "persistent_regime"),
            ("coherent_assessment", coherence_class == "coherent"),
            ("no_anomaly_detected", anomaly_class == "no_anomaly"),
            ("no_blocked_signals", not blocked_condition),
        ) if ok
    ]
    risk_factors = [
        factor for factor, ok in (
            ("positive_net_severity_delta", net_delta > 0),
            ("blocked_condition", blocked_condition),
            ("incoherent_condition", incoherent_condition),
            ("degraded_condition", degraded_condition),
            ("fragile_condition", fragile_condition),
            ("weakly_stable_condition", weakly_stable_condition),
            ("invalid_signal_detected", out_class == "invalid_stability_input"),
            ("insufficient_history", out_class == "insufficient_history"),
        ) if ok
    ]

    result = {
        "stability_resilience_class": out_class,
        "state_count": len(state_path),
        "transition_count": len(transition_path),
        "initial_state": initial_state,
        "latest_state": latest_state,
        "dominant_state": dominant_state,
        "initial_severity_rank": initial_rank,
        "latest_severity_rank": latest_rank,
        "net_severity_delta": net_delta,
        "max_severity_jump": max_severity_jump,
        "severity_path": severity_path,
        "transition_class_path": [t for t in transition_path if isinstance(t, str)],
        "drift_class": drift_class,
        "continuity_class": continuity_class,
        "regime_persistence_class": regime_class,
        "anomaly_attribution_class": anomaly_class,
        "coherence_class": coherence_class,
        "resilience_factors": resilience_factors,
        "risk_factors": risk_factors,
        "resilience_factor_count": len(resilience_factors),
        "risk_factor_count": len(risk_factors),
        "deterministic_evidence_summary": {
            "malformed_input": malformed_input,
            "invalid_state_count": invalid_state_count,
            "invalid_transition_count": invalid_transition_count,
            "invalid_drift_count": invalid_drift_count,
            "invalid_continuity_count": invalid_continuity_count,
            "invalid_regime_count": invalid_regime_count,
            "invalid_anomaly_count": invalid_anomaly_count,
            "invalid_coherence_count": invalid_coherence_count,
            "latest_transition_class": latest_transition,
            "structural_evidence_keys": sorted(str(k) for k in evidence_safe.keys()),
            "decision_rule": rule,
        },
        "fixed_template_explanation": (
            "Strategic stability/resilience intelligence is deterministic: "
            f"stability_resilience_class={out_class}; state_count={len(state_path)}; transition_count={len(transition_path)}; "
            f"initial_state={initial_state}; latest_state={latest_state}; dominant_state={dominant_state}; "
            f"drift_class={drift_class}; continuity_class={continuity_class}; regime_persistence_class={regime_class}; "
            f"anomaly_attribution_class={anomaly_class}; coherence_class={coherence_class}; net_severity_delta={net_delta}; "
            f"max_severity_jump={max_severity_jump}; rule={rule}."
        ),
        "precedence_metadata": {
            "ordering": list(STABILITY_RESILIENCE_PRECEDENCE),
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
    result["strategic_stability_resilience_checksum"] = stable_checksum(
        {k: result[k] for k in result if k != "strategic_stability_resilience_checksum"},
        prefix="tier7h_strategic_stability_resilience",
    )
    return result


__all__ = [
    "STABILITY_RESILIENCE_CLASSES",
    "STABILITY_RESILIENCE_PRECEDENCE",
    "assess_strategic_stability_resilience",
]
