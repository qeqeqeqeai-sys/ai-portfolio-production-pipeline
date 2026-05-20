from __future__ import annotations

from typing import Any


def _bound01(value: float) -> float:
    return max(0.0, min(1.0, round(float(value), 6)))


def detect_tipping_points(fragility_states: list[dict[str, Any]], jump_threshold: float = 0.12) -> dict[str, Any]:
    jt = _bound01(jump_threshold)
    states = [dict(s) for s in fragility_states]
    points = []
    previous = _bound01(float(states[0].get("system_fragility_score", 0.0))) if states else 0.0
    for idx, state in enumerate(states[1:], start=1):
        current = _bound01(float(state.get("system_fragility_score", 0.0)))
        delta = round(current - previous, 6)
        if delta >= jt:
            points.append({"step": idx, "fragility_score": current, "delta": delta, "kind": "positive_jump"})
        previous = current

    return {
        "tipping_points": points,
        "tipping_point_count": len(points),
        "jump_threshold": jt,
        "max_jump_delta": max((p["delta"] for p in points), default=0.0),
        "first_tipping_step": points[0]["step"] if points else -1,
    }
