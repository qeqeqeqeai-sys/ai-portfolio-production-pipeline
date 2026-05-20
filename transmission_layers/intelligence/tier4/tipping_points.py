from __future__ import annotations

from typing import Any


def _b(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 6)


def detect_tipping_points(fragility_states: list[dict[str, Any]], jump_threshold: float = 0.12) -> dict[str, Any]:
    jt = _b(jump_threshold)
    states = [dict(s) for s in fragility_states]
    points = []
    previous = 0.0
    for idx, state in enumerate(states):
        current = _b(float(state.get("system_fragility_score", 0.0)))
        delta = _b(current - previous)
        if idx > 0 and delta >= jt:
            points.append({"step": idx, "fragility_score": current, "delta": delta})
        previous = current
    return {"tipping_points": points, "tipping_point_count": len(points), "jump_threshold": jt}
