from __future__ import annotations
from typing import Any
from .cascade_signatures import compute_cascade_corridor_checksum

def _bound01(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))

def score_cascade_corridors(edges: list[dict[str, Any]], node_stress: dict[str, float]) -> dict[str, Any]:
    scored = []
    for e in sorted(edges, key=lambda x: (str(x.get("source_node_id", "")), str(x.get("target_node_id", "")))):
        cid = f"{e.get('source_node_id','')}->{e.get('target_node_id','')}"
        stress = max(float(node_stress.get(str(e.get("source_node_id", "")), 0.0)), float(node_stress.get(str(e.get("target_node_id", "")), 0.0)))
        score = _bound01(0.7 * stress + 0.3 * (1.0 - float(e.get("edge_quality_score", 0.0))))
        scored.append((cid, score))
    corridor = _bound01(sum(v for _, v in scored) / len(scored) if scored else 0.0)
    out = {"cascade_corridor_score": corridor, "corridor_rankings": scored}
    out["cascade_corridor_checksum"] = compute_cascade_corridor_checksum(out)
    return out
