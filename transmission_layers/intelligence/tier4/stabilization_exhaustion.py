from __future__ import annotations

from typing import Any

from .resistance_signatures import compute_exhaustion_checksum


def _bound01(value: float) -> float:
    return max(0.0, min(1.0, round(float(value), 6)))


def detect_stabilization_exhaustion(pressure: dict[str, Any], threshold: float = 0.65) -> dict[str, Any]:
    ranked = []
    for row in sorted(pressure.get("pressure_resistance_ranking", []), key=lambda r: str(r.get("node_id", ""))):
        exhaustion = _bound01(float(row.get("exhaustion_score", 0.0)))
        ranked.append({"node_id": str(row.get("node_id", "")), "exhaustion_score": exhaustion, "exhaustion_detected": exhaustion >= _bound01(threshold)})
    out = {"exhaustion_ranking": ranked, "exhaustion_score": _bound01(sum(r["exhaustion_score"] for r in ranked) / max(1, len(ranked))), "exhausted_nodes": [r["node_id"] for r in ranked if r["exhaustion_detected"]]}
    out["exhaustion_checksum"] = compute_exhaustion_checksum(out)
    return out
