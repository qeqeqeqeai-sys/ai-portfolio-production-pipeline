from __future__ import annotations


def _bound01(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))


def score_flexibility_collapse(adaptation_constraint_score: float, resilience_saturation_score: float) -> dict[str, float | bool]:
    score = _bound01(0.5 * _bound01(adaptation_constraint_score) + 0.5 * _bound01(resilience_saturation_score))
    return {"flexibility_collapse_score": score, "flexibility_collapse_detected": score >= 0.65}
