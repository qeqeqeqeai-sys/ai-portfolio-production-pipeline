from __future__ import annotations

from typing import Any

from .fragility_signatures import compute_fragility_checksum


def _b(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 6)


def compute_fragility_scores(node_states: list[dict[str, Any]]) -> dict[str, Any]:
    ranked = []
    for state in sorted(node_states, key=lambda s: str(s.get("node_id", ""))):
        node_id = str(state.get("node_id", ""))
        overload = _b(float(state.get("overload", 0.0)))
        resilience = _b(float(state.get("resilience", 0.0)))
        fragmentation = _b(float(state.get("fragmentation", 0.0)))
        cascade_amplification = _b(float(state.get("cascade_amplification", overload * fragmentation)))
        relapse_persistence = _b(float(state.get("relapse_persistence", 1.0 - resilience)))
        fragility = _b((overload * 0.35) + ((1.0 - resilience) * 0.30) + (fragmentation * 0.20) + (cascade_amplification * 0.10) + (relapse_persistence * 0.05))
        ranked.append({
            "node_id": node_id,
            "fragility_score": fragility,
            "overload_contribution": overload,
            "resilience": resilience,
            "fragmentation_contribution": fragmentation,
            "cascade_amplification": cascade_amplification,
            "relapse_persistence": relapse_persistence,
        })
    ranked = sorted(
        ranked,
        key=lambda x: (
            -x["overload_contribution"],
            x["resilience"],
            -x["fragmentation_contribution"],
            -x["cascade_amplification"],
            -x["relapse_persistence"],
            x["node_id"],
        ),
    )
    system_fragility = _b(sum(x["fragility_score"] for x in ranked) / max(1, len(ranked)))
    out = {"node_fragility_ranking": ranked, "system_fragility_score": system_fragility, "node_count": len(ranked)}
    out["fragility_checksum"] = compute_fragility_checksum(out)
    return out
