from __future__ import annotations


def _bound01(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))


def score_resilience_saturation(resilience_score: float, adaptation_constraint_score: float) -> dict[str, float | bool]:
    score = _bound01(0.7 * (1.0 - _bound01(resilience_score)) + 0.3 * _bound01(adaptation_constraint_score))
    return {"resilience_saturation_score": score, "resilience_saturation_detected": score >= 0.6}
