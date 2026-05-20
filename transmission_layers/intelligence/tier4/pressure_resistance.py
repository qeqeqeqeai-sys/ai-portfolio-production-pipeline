from __future__ import annotations

from typing import Any

from .resistance_signatures import compute_pressure_resistance_checksum


def _bound01(value: float) -> float:
    return max(0.0, min(1.0, round(float(value), 6)))


def compute_pressure_resistance(capacity: dict[str, Any], pressure_id: str = "tier4_pressure_resistance") -> dict[str, Any]:
    ranking = []
    for row in sorted(capacity.get("node_capacity_ranking", []), key=lambda r: str(r.get("node_id", ""))):
        margin = _bound01(float(row.get("absorption_margin", 0.0)))
        exhaustion = _bound01(float(row.get("exhaustion_score", 0.0)))
        saturation = _bound01(float(row.get("saturation_score", 0.0)))
        durability = _bound01(float(row.get("resistance_durability_score", 0.0)))
        resistance = _bound01(margin * 0.4 + durability * 0.4 + (1.0 - max(exhaustion, saturation)) * 0.2)
        ranking.append({**dict(row), "pressure_resistance_score": resistance, "resistance_checksum": ""})
    ranking = sorted(ranking, key=lambda x: (x["absorption_margin"], -x["exhaustion_score"], -x["saturation_score"], x["resistance_durability_score"], -x.get("fragility_score", 0.0), x["node_id"]))
    out = {
        "capacity_id": str(capacity.get("capacity_id", "")),
        "pressure_id": pressure_id,
        "pressure_resistance_ranking": ranking,
        "pressure_resistance_score": _bound01(sum(x["pressure_resistance_score"] for x in ranking) / max(1, len(ranking))),
        "absorption_margin": _bound01(sum(x["absorption_margin"] for x in ranking) / max(1, len(ranking))),
    }
    out["pressure_resistance_checksum"] = compute_pressure_resistance_checksum(out)
    return out
