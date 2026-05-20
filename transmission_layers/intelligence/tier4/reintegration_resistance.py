from __future__ import annotations


def _bound01(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))


def score_reintegration_resistance(flexibility_collapse_score: float, resilience_score: float) -> dict[str, float | bool]:
    score = _bound01(0.65 * _bound01(flexibility_collapse_score) + 0.35 * (1.0 - _bound01(resilience_score)))
    return {"reintegration_resistance_score": score, "reintegration_resistance_detected": score >= 0.6}
