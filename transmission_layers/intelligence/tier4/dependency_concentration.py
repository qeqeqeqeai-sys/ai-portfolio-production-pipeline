from __future__ import annotations
from .cascade_signatures import compute_dependency_concentration_checksum

def _bound01(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))

def score_dependency_concentration(edges: list[dict]) -> dict:
    outgoing = {}
    total = 0
    for e in edges:
        src = str(e.get("source_node_id", ""))
        outgoing[src] = outgoing.get(src, 0) + 1
        total += 1
    top = max(outgoing.values()) if outgoing else 0
    score = _bound01(top / total) if total else 0.0
    out = {"dependency_concentration_score": score}
    out["dependency_concentration_checksum"] = compute_dependency_concentration_checksum(out)
    return out
