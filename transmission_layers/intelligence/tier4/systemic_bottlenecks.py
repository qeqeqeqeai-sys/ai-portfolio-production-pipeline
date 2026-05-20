from __future__ import annotations
from typing import Any
from .cascade_signatures import compute_bottleneck_checksum

def _bound01(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))

def score_systemic_bottlenecks(nodes: list[dict[str, Any]], node_stress: dict[str, float]) -> dict[str, Any]:
    vals = []
    for n in sorted(nodes, key=lambda x: str(x.get("node_id", ""))):
        nid = str(n.get("node_id", ""))
        vals.append(_bound01(0.5 * float(node_stress.get(nid, 0.0)) + 0.3 * float(n.get("chokepoint_score", 0.0)) + 0.2 * float(n.get("traffic_score", 0.0))))
    score = _bound01(sum(vals)/len(vals) if vals else 0.0)
    out = {"systemic_bottleneck_score": score}
    out["bottleneck_checksum"] = compute_bottleneck_checksum(out)
    return out
