from __future__ import annotations

from typing import Any


def _bound01(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))


def score_regeneration_pathways(nodes: list[dict[str, Any]], replay_window: list[dict[str, float]]) -> dict[str, Any]:
    node_ids = sorted(str(n.get("node_id", "")) for n in nodes)
    if not node_ids or not replay_window:
        return {"regeneration_pathway_score": 0.0, "regeneration_detected": False, "node_regeneration": []}
    node_scores = []
    for node_id in node_ids:
        series = [float(frame.get(node_id, 0.0)) for frame in replay_window]
        improvement = _bound01(max(0.0, series[-1] - series[0]))
        continuity = _bound01(sum(1.0 for i in range(1, len(series)) if series[i] >= series[i - 1]) / max(1, len(series) - 1))
        score = _bound01(0.6 * improvement + 0.4 * continuity)
        node_scores.append((node_id, score))
    pathway_score = _bound01(sum(s for _, s in node_scores) / len(node_scores))
    return {
        "regeneration_pathway_score": pathway_score,
        "regeneration_detected": pathway_score >= 0.5,
        "node_regeneration": node_scores,
    }
