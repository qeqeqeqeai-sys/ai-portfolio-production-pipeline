from __future__ import annotations

from typing import Any


def _bound01(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))


def _to_float(v: Any, d: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def score_adaptation_constraints(node: dict[str, Any], replay_window: list[dict[str, float]]) -> dict[str, Any]:
    node_id = str(node.get("node_id", ""))
    series = [_bound01(float(snapshot.get(node_id, 0.0))) for snapshot in replay_window]
    span = max(series) - min(series) if series else 0.0
    score = _bound01(0.55 * (1.0 - span) + 0.45 * _to_float(node.get("load_score"), 0.0))
    return {"adaptation_constraint_score": score, "adaptation_constraint_detected": score >= 0.6}
