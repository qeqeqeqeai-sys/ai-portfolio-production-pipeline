from __future__ import annotations

from typing import Any

from .resistance_signatures import compute_saturation_checksum


def _bound01(value: float) -> float:
    return max(0.0, min(1.0, round(float(value), 6)))


def detect_intervention_saturation(pressure: dict[str, Any], threshold: float = 0.6) -> dict[str, Any]:
    ranked = []
    for row in sorted(pressure.get("pressure_resistance_ranking", []), key=lambda r: str(r.get("node_id", ""))):
        sat = _bound01(float(row.get("saturation_score", 0.0)))
        rec_fatigue = sat >= 0.5 and _bound01(float(row.get("resistance_durability_score", 0.0))) < 0.5
        ranked.append({"node_id": str(row.get("node_id", "")), "saturation_score": sat, "saturation_detected": sat >= _bound01(threshold), "recovery_fatigue_detected": rec_fatigue})
    out = {"saturation_ranking": ranked, "saturation_score": _bound01(sum(r["saturation_score"] for r in ranked) / max(1, len(ranked))), "saturated_nodes": [r["node_id"] for r in ranked if r["saturation_detected"]]}
    out["saturation_checksum"] = compute_saturation_checksum(out)
    return out
