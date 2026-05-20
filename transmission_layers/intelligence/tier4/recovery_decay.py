from __future__ import annotations

from typing import Any, Dict, List

from .recovery_signatures import compute_recovery_decay_checksum


def _bound01(value: float) -> float:
    return max(0.0, min(1.0, round(float(value), 6)))


def detect_structural_relapse(recovery_states: List[Dict[str, Any]], threshold: float = 0.15) -> Dict[str, Any]:
    bounded_threshold = _bound01(threshold)
    if len(recovery_states) < 2:
        return {"relapse_detected": False, "relapse_score": 0.0, "relapse_factors": []}
    factors: List[tuple[str, float]] = []
    resilience_drop = _bound01(float(recovery_states[0].get("resilience", 0.0))) - _bound01(float(recovery_states[-1].get("resilience", 0.0)))
    overload_rise = _bound01(float(recovery_states[-1].get("overload", 0.0))) - _bound01(float(recovery_states[0].get("overload", 0.0)))
    fragmentation_rise = _bound01(float(recovery_states[-1].get("fragmentation", 0.0))) - _bound01(float(recovery_states[0].get("fragmentation", 0.0)))
    for key, val in [("fragmentation", fragmentation_rise), ("overload", overload_rise), ("resilience", resilience_drop)]:
        factors.append((key, max(0.0, round(val, 6))))
    factors = sorted(factors, key=lambda x: (-x[1], x[0]))
    relapse_score = _bound01(sum(v for _, v in factors) / len(factors))
    return {
        "relapse_detected": relapse_score >= bounded_threshold,
        "relapse_score": relapse_score,
        "relapse_factors": factors,
    }


def compute_recovery_decay(recovery_states: List[Dict[str, Any]]) -> Dict[str, Any]:
    relapse = detect_structural_relapse(recovery_states)
    if not recovery_states:
        out = {"decay_curve": [], "dominant_decay_factor": "none", **relapse}
        out["recovery_decay_checksum"] = compute_recovery_decay_checksum(out)
        return out
    decay_curve = []
    first = recovery_states[0]
    for i, state in enumerate(recovery_states):
        decay_curve.append(
            {
                "step": i,
                "resilience_decay": _bound01(_bound01(float(first.get("resilience", 0.0))) - _bound01(float(state.get("resilience", 0.0)))),
                "overload_decay": _bound01(_bound01(float(state.get("overload", 0.0))) - _bound01(float(first.get("overload", 0.0)))),
                "fragmentation_decay": _bound01(_bound01(float(state.get("fragmentation", 0.0))) - _bound01(float(first.get("fragmentation", 0.0)))),
            }
        )
    dominant = relapse["relapse_factors"][0][0] if relapse["relapse_factors"] else "none"
    out = {"decay_curve": decay_curve, "dominant_decay_factor": dominant, **relapse}
    out["recovery_decay_checksum"] = compute_recovery_decay_checksum(out)
    return out


def summarize_recovery_decay(decay: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "relapse_detected": bool(decay.get("relapse_detected", False)),
        "relapse_score": _bound01(decay.get("relapse_score", 0.0)),
        "dominant_decay_factor": str(decay.get("dominant_decay_factor", "none")),
        "recovery_decay_checksum": str(decay.get("recovery_decay_checksum", "")),
    }


def compute_resilience_half_life(recovery_states: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not recovery_states:
        return {"half_life_step": 0, "half_life_found": False, "window_size": 0}
    initial = _bound01(float(recovery_states[0].get("resilience", 0.0)))
    target = initial / 2.0
    step = 0
    found = False
    for i, state in enumerate(recovery_states):
        if _bound01(float(state.get("resilience", 0.0))) <= target:
            step = i
            found = True
            break
    if not found:
        step = len(recovery_states)
    return {"half_life_step": int(step), "half_life_found": found, "window_size": len(recovery_states)}


def summarize_resilience_half_life(half_life: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "half_life_step": int(half_life.get("half_life_step", 0)),
        "half_life_found": bool(half_life.get("half_life_found", False)),
        "window_size": int(half_life.get("window_size", 0)),
    }
