from __future__ import annotations

from typing import Any

from .transition_signatures import compute_stress_clustering_checksum


def _b(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))


def compute_systemic_stress_clustering(node_states: list[dict[str, Any]]) -> dict[str, Any]:
    nodes = sorted((dict(s) for s in node_states), key=lambda x: str(x.get("node_id", "")))
    if not nodes:
        out = {"systemic_stress_clustering_score": 0.0, "systemic_stress_cluster_detected": False}
        out["stress_clustering_checksum"] = compute_stress_clustering_checksum(out)
        return out
    stressed = sum(1 for n in nodes if _b(n.get("stress", n.get("propagated_stress", 0.0))) >= 0.7)
    score = _b(stressed / len(nodes))
    out = {"systemic_stress_clustering_score": score, "systemic_stress_cluster_detected": score >= 0.4}
    out["stress_clustering_checksum"] = compute_stress_clustering_checksum(out)
    return out
