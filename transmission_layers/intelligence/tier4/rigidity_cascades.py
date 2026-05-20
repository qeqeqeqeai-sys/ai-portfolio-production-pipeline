from __future__ import annotations


def _bound01(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))


def score_rigidity_cascades(neighbor_scores: list[float], flexibility_collapse_score: float) -> dict[str, float | bool]:
    neighbor_avg = _bound01(sum(_bound01(x) for x in neighbor_scores) / len(neighbor_scores)) if neighbor_scores else 0.0
    score = _bound01(0.6 * neighbor_avg + 0.4 * _bound01(flexibility_collapse_score))
    return {"rigidity_cascade_score": score, "rigidity_cascade_detected": score >= 0.6}
