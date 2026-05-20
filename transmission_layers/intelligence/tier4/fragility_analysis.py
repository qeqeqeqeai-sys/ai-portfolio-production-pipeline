from __future__ import annotations

from typing import Any

from .fragility_signatures import compute_fragility_checksum


def _bound01(value: float) -> float:
    return max(0.0, min(1.0, round(float(value), 6)))


def _classify(score: float) -> str:
    if score >= 0.8:
        return "critical"
    if score >= 0.6:
        return "elevated"
    if score >= 0.35:
        return "watch"
    return "stable"


def _node_fragility(state: dict[str, Any]) -> dict[str, Any]:
    node_id = str(state.get("node_id", ""))
    overload = _bound01(float(state.get("overload", 0.0)))
    resilience = _bound01(float(state.get("resilience", 0.0)))
    fragmentation = _bound01(float(state.get("fragmentation", 0.0)))
    cascade_amplification = _bound01(float(state.get("cascade_amplification", overload * fragmentation)))
    relapse_persistence = _bound01(float(state.get("relapse_persistence", 1.0 - resilience)))
    fragility_score = _bound01(
        overload * 0.35
        + (1.0 - resilience) * 0.30
        + fragmentation * 0.20
        + cascade_amplification * 0.10
        + relapse_persistence * 0.05
    )
    return {
        "node_id": node_id,
        "fragility_score": fragility_score,
        "overload_contribution": overload,
        "resilience": resilience,
        "fragmentation_contribution": fragmentation,
        "cascade_amplification": cascade_amplification,
        "relapse_persistence": relapse_persistence,
    }


def compute_fragility_scores(node_states: list[dict[str, Any]], fragility_id: str = "tier4_fragility") -> dict[str, Any]:
    ranked = [_node_fragility(s) for s in sorted(node_states, key=lambda s: str(s.get("node_id", "")))]
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

    system_fragility = _bound01(sum(x["fragility_score"] for x in ranked) / max(1, len(ranked)))
    dominant = ranked[0] if ranked else {}
    out = {
        "fragility_id": fragility_id,
        "node_fragility_ranking": ranked,
        "fragility_score": system_fragility,
        "bounded_fragility_score": system_fragility,
        "system_fragility_score": system_fragility,
        "dominant_fragility_factor": "overload" if dominant else "none",
        "fragility_classification": _classify(system_fragility),
        "threshold_proximity_score": _bound01(system_fragility / 0.65),
        "structural_survivability_score": _bound01(1.0 - system_fragility),
        "node_count": len(ranked),
        "top_fragility_node": str(dominant.get("node_id", "")),
    }
    out["fragility_checksum"] = compute_fragility_checksum(out)
    return out


def compare_fragility_scores(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    return {
        "system_fragility_delta": _bound01((float(a.get("system_fragility_score", 0.0)) - float(b.get("system_fragility_score", 0.0))) / 2.0) * 2.0,
        "same_checksum": str(a.get("fragility_checksum", "")) == str(b.get("fragility_checksum", "")),
        "same_top_node": str(a.get("top_fragility_node", "")) == str(b.get("top_fragility_node", "")),
    }


def summarize_fragility_scores(fragility: dict[str, Any]) -> dict[str, Any]:
    return {
        "fragility_id": str(fragility.get("fragility_id", "")),
        "fragility_score": _bound01(float(fragility.get("fragility_score", 0.0))),
        "bounded_fragility_score": _bound01(float(fragility.get("bounded_fragility_score", 0.0))),
        "dominant_fragility_factor": str(fragility.get("dominant_fragility_factor", "none")),
        "fragility_classification": str(fragility.get("fragility_classification", "stable")),
        "structural_survivability_score": _bound01(float(fragility.get("structural_survivability_score", 0.0))),
        "threshold_proximity_score": _bound01(float(fragility.get("threshold_proximity_score", 0.0))),
        "fragility_checksum": str(fragility.get("fragility_checksum", "")),
    }
