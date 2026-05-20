from __future__ import annotations

from typing import Any, Dict, List


def _bound01(value: float) -> float:
    return max(0.0, min(1.0, round(float(value), 6)))


def compute_stabilization_persistence(recovery_states: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not recovery_states:
        return {
            "persistence_score": 0.0,
            "stabilization_duration": 0,
            "bounded_persistence_delta": 0.0,
            "persistence_classification": "unbounded",
        }
    resilience = [_bound01(float(s.get("resilience", 0.0))) for s in recovery_states]
    overload = [_bound01(float(s.get("overload", 1.0))) for s in recovery_states]
    state_scores = [_bound01((r + (1.0 - o)) / 2.0) for r, o in zip(resilience, overload)]
    persistence_score = _bound01(sum(state_scores) / len(state_scores))
    base_delta = state_scores[-1] - state_scores[0]
    bounded_delta = max(-1.0, min(1.0, round(base_delta, 6)))
    stabilization_duration = sum(1 for s in state_scores if s >= 0.6)
    classification = "stable" if persistence_score >= 0.7 else "partial" if persistence_score >= 0.4 else "unbounded"
    return {
        "persistence_score": persistence_score,
        "stabilization_duration": int(stabilization_duration),
        "bounded_persistence_delta": bounded_delta,
        "persistence_classification": classification,
    }


def evaluate_recovery_persistence(recovery_states: List[Dict[str, Any]]) -> Dict[str, Any]:
    metrics = compute_stabilization_persistence(recovery_states)
    metrics["recovery_consistency_valid"] = bool(metrics["stabilization_duration"] <= len(recovery_states))
    return metrics


def summarize_recovery_persistence(persistence: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "persistence_score": _bound01(persistence.get("persistence_score", 0.0)),
        "stabilization_duration": int(persistence.get("stabilization_duration", 0)),
        "persistence_classification": str(persistence.get("persistence_classification", "unbounded")),
    }
