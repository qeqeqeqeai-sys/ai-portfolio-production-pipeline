from __future__ import annotations

from typing import Any


def _bound01(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))


def score_recovery_bottlenecks(nodes: list[dict[str, Any]], node_recovery: dict[str, float]) -> dict[str, Any]:
    scored = []
    for n in sorted(nodes, key=lambda x: str(x.get("node_id", ""))):
        node_id = str(n.get("node_id", ""))
        chokepoint = float(n.get("chokepoint_score", 0.0))
        rec = float(node_recovery.get(node_id, 0.0))
        score = _bound01(0.7 * (1.0 - rec) + 0.3 * chokepoint)
        scored.append((node_id, score))
    bottleneck_score = _bound01(sum(v for _, v in scored) / len(scored) if scored else 0.0)
    return {"recovery_bottleneck_score": bottleneck_score, "recovery_bottleneck_detected": bottleneck_score >= 0.5, "node_bottlenecks": scored}
