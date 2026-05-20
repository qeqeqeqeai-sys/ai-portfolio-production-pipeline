from __future__ import annotations
from typing import Any
from .cascade_signatures import compute_structural_criticality_checksum


def _to_float(v: Any, d: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def _bound01(value: float) -> float:
    return max(0.0, min(1.0, round(float(value), 6)))


def score_structural_criticality(node: dict[str, Any]) -> dict[str, Any]:
    score = _bound01(
        0.30 * _to_float(node.get("influence_score"))
        + 0.25 * _to_float(node.get("chokepoint_score"))
        + 0.20 * _to_float(node.get("contagion_score"))
        + 0.15 * _to_float(node.get("traffic_score"))
        + 0.10 * (1.0 - _to_float(node.get("resilience_score"), 0.5))
    )
    out = {
        "cascade_id": str(node.get("cascade_id", node.get("node_id", "tier4m_cascade"))),
        "structural_criticality_score": score,
        "bounded_structural_criticality_score": score,
    }
    out["structural_criticality_checksum"] = compute_structural_criticality_checksum(out)
    return out
