from __future__ import annotations


def _bound01(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))


def score_reintegration_stability(recovery_score: float, fragmentation_score: float, bottleneck_score: float) -> dict[str, float | bool]:
    score = _bound01(0.5 * recovery_score + 0.3 * (1.0 - fragmentation_score) + 0.2 * (1.0 - bottleneck_score))
    return {"reintegration_stability_score": score, "reintegration_stability_detected": score >= 0.5}
