from __future__ import annotations

from typing import Any

from .resistance_signatures import compute_capacity_checksum


def _bound01(value: float) -> float:
    return max(0.0, min(1.0, round(float(value), 6)))


def _classify(score: float) -> str:
    if score >= 0.75:
        return "durable"
    if score >= 0.5:
        return "temporarily_stabilized"
    if score >= 0.3:
        return "pressure_sensitive"
    return "brittle"


def compute_stabilization_capacity(node_states: list[dict[str, Any]], capacity_id: str = "tier4_stabilization_capacity") -> dict[str, Any]:
    ranked = []
    for state in sorted(node_states, key=lambda s: str(s.get("node_id", ""))):
        node_id = str(state.get("node_id", ""))
        stress = _bound01(float(state.get("propagated_stress", state.get("overload", 0.0))))
        resilience = _bound01(float(state.get("resilience", 0.0)))
        intervention = _bound01(float(state.get("intervention_effectiveness", resilience)))
        fragility = _bound01(float(state.get("fragility_score", 1.0 - resilience)))
        absorption_margin = _bound01(1.0 - stress)
        stabilization_capacity_score = _bound01(absorption_margin * 0.45 + resilience * 0.35 + intervention * 0.20)
        bounded_capacity_score = stabilization_capacity_score
        exhaustion_score = _bound01(1.0 - stabilization_capacity_score)
        saturation_score = _bound01(stress * (1.0 - intervention))
        durability = _bound01(resilience * 0.5 + absorption_margin * 0.3 + intervention * 0.2)
        ranked.append({
            "capacity_id": f"{capacity_id}:{node_id}",
            "node_id": node_id,
            "stabilization_capacity_score": stabilization_capacity_score,
            "bounded_capacity_score": bounded_capacity_score,
            "absorption_margin": absorption_margin,
            "exhaustion_score": exhaustion_score,
            "saturation_score": saturation_score,
            "resistance_durability_score": durability,
            "dominant_capacity_factor": "absorption_margin" if absorption_margin >= resilience else "resilience",
            "capacity_classification": _classify(stabilization_capacity_score),
            "fragility_score": fragility,
        })
    ranked = sorted(ranked, key=lambda x: (x["absorption_margin"], -x["exhaustion_score"], -x["saturation_score"], x["resistance_durability_score"], -x.get("fragility_score", 0.0), x["node_id"]))
    system_score = _bound01(sum(x["stabilization_capacity_score"] for x in ranked) / max(1, len(ranked)))
    out = {"capacity_id": capacity_id, "node_capacity_ranking": ranked, "stabilization_capacity_score": system_score, "bounded_capacity_score": system_score, "node_count": len(ranked)}
    out["capacity_checksum"] = compute_capacity_checksum(out)
    return out
