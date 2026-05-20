from __future__ import annotations

from typing import Any


def _bound01(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))


def score_recovery_corridors(edges: list[dict[str, Any]], node_recovery: dict[str, float]) -> dict[str, Any]:
    rankings: list[tuple[str, float]] = []
    for edge in sorted(edges, key=lambda x: (str(x.get("source_node_id", "")), str(x.get("target_node_id", "")))):
        source = str(edge.get("source_node_id", ""))
        target = str(edge.get("target_node_id", ""))
        quality = float(edge.get("edge_quality_score", 0.0))
        recovered = min(float(node_recovery.get(source, 0.0)), float(node_recovery.get(target, 0.0)))
        score = _bound01(0.65 * recovered + 0.35 * quality)
        rankings.append((f"{source}->{target}", score))
    corridor_score = _bound01(sum(v for _, v in rankings) / len(rankings) if rankings else 0.0)
    return {
        "recovery_corridor_score": corridor_score,
        "recovery_corridor_detected": corridor_score >= 0.5,
        "corridor_rankings": rankings,
    }
