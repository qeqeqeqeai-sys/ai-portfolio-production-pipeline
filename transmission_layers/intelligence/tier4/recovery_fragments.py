from __future__ import annotations

from typing import Any


def _bound01(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))


def score_recovery_fragments(edges: list[dict[str, Any]], node_recovery: dict[str, float]) -> dict[str, Any]:
    if not edges:
        return {"recovery_fragmentation_score": 0.0, "recovery_fragmentation_detected": False, "fragmented_links": []}
    fragments = []
    for e in sorted(edges, key=lambda x: (str(x.get("source_node_id", "")), str(x.get("target_node_id", "")))):
        s = str(e.get("source_node_id", ""))
        t = str(e.get("target_node_id", ""))
        gap = abs(float(node_recovery.get(s, 0.0)) - float(node_recovery.get(t, 0.0)))
        if gap >= 0.35:
            fragments.append((f"{s}->{t}", _bound01(gap)))
    frag_score = _bound01(sum(v for _, v in fragments) / len(edges))
    return {"recovery_fragmentation_score": frag_score, "recovery_fragmentation_detected": frag_score >= 0.3, "fragmented_links": fragments}
