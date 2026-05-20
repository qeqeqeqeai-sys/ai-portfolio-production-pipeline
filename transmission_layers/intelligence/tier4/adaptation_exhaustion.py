from __future__ import annotations


def _bound01(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))


def score_adaptation_exhaustion(adaptation_constraint_score: float, reintegration_resistance_score: float) -> dict[str, float | bool]:
    score = _bound01(0.5 * _bound01(adaptation_constraint_score) + 0.5 * _bound01(reintegration_resistance_score))
    return {"adaptation_exhaustion_score": score, "adaptation_exhaustion_detected": score >= 0.6}
