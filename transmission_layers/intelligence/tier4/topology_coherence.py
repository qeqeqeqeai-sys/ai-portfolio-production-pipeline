from __future__ import annotations

from typing import Any

from .transition_signatures import compute_topology_coherence_checksum


def _b(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))


def compute_topology_coherence(node_states: list[dict[str, Any]], corridors: list[dict[str, Any]]) -> dict[str, Any]:
    nodes = sorted((dict(s) for s in node_states), key=lambda x: str(x.get("node_id", "")))
    edges = sorted((dict(c) for c in corridors), key=lambda x: (str(x.get("from", "")), str(x.get("to", ""))))
    if not nodes:
        out = {"topology_coherence_score": 1.0, "topology_coherence_degradation_detected": False}
        out["topology_coherence_checksum"] = compute_topology_coherence_checksum(out)
        return out
    incident = {str(n.get("node_id", "")): 0 for n in nodes}
    for e in edges:
        a, b = str(e.get("from", "")), str(e.get("to", ""))
        if a in incident:
            incident[a] += 1
        if b in incident:
            incident[b] += 1
    disconnected = sum(1 for n, d in sorted(incident.items()) if d == 0)
    suppression = [_b(e.get("suppression", 0.0)) for e in edges] if edges else [1.0]
    score = _b(1.0 - ((disconnected / len(nodes)) * 0.7 + (sum(suppression) / len(suppression)) * 0.3))
    out = {"topology_coherence_score": score, "topology_coherence_degradation_detected": score < 0.6}
    out["topology_coherence_checksum"] = compute_topology_coherence_checksum(out)
    return out
