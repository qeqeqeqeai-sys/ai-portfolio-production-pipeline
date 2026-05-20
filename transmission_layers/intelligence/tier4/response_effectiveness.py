from __future__ import annotations

from typing import Any, Dict

from .scenario_semantics import clamp_score
from .response_signatures import compute_response_effectiveness_checksum


WEIGHTS = {
    "overload_reduction": 0.3,
    "fragmentation_reduction": 0.2,
    "resilience_improvement": 0.2,
    "cascade_suppression_improvement": 0.15,
    "regime_stabilization_improvement": 0.15,
}


def _metric(state: Dict[str, Any]) -> Dict[str, float]:
    nodes = state.get("structural_influence_nodes", [])
    edges = state.get("quality_scored_edges", [])
    n = max(1, len(nodes))
    e = max(1, len(edges))
    overload = clamp_score(sum(float(x.get("traffic_score", 0.0)) for x in nodes) / n)
    resilience = clamp_score(sum(float(x.get("resilience_score", 0.0)) for x in nodes) / n)
    cascade = clamp_score(sum(float(x.get("contagion_score", 0.0)) for x in nodes) / n)
    frag = clamp_score(1.0 - (sum(float(x.get("edge_quality_score", 0.0)) for x in edges) / e))
    return {"overload": overload, "fragmentation": frag, "resilience": resilience, "cascade": cascade, "regime_stability": clamp_score((resilience + (1.0 - overload)) / 2.0)}


def _delta(before: float, after: float, inverse: bool = False) -> float:
    raw = (before - after) if inverse else (after - before)
    return max(-1.0, min(1.0, round(raw, 6)))


def compute_response_effectiveness(before_state: Dict[str, Any], after_state: Dict[str, Any]) -> Dict[str, Any]:
    b, a = _metric(before_state), _metric(after_state)
    deltas = {
        "overload_reduction": _delta(b["overload"], a["overload"], inverse=True),
        "fragmentation_reduction": _delta(b["fragmentation"], a["fragmentation"], inverse=True),
        "resilience_improvement": _delta(b["resilience"], a["resilience"]),
        "cascade_suppression_improvement": _delta(b["cascade"], a["cascade"], inverse=True),
        "regime_stabilization_improvement": _delta(b["regime_stability"], a["regime_stability"]),
    }
    normalized = {k: clamp_score((v + 1.0) / 2.0) for k, v in deltas.items()}
    score = clamp_score(sum(normalized[k] * WEIGHTS[k] for k in WEIGHTS))
    out = {"effectiveness_deltas": deltas, "effectiveness_components": normalized, "response_effectiveness_score": score}
    out["response_effectiveness_checksum"] = compute_response_effectiveness_checksum(out)
    return out


def compare_response_effectiveness(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    return {"score_delta": max(-1.0, min(1.0, round(float(a.get("response_effectiveness_score", 0.0)) - float(b.get("response_effectiveness_score", 0.0)), 6))), "same_checksum": a.get("response_effectiveness_checksum") == b.get("response_effectiveness_checksum")}


def summarize_response_effectiveness(effectiveness: Dict[str, Any]) -> Dict[str, Any]:
    return {"response_effectiveness_score": clamp_score(effectiveness.get("response_effectiveness_score", 0.0)), "dominant_response_factor": sorted(effectiveness.get("effectiveness_deltas", {}).items(), key=lambda kv: (-kv[1], kv[0]))[0][0] if effectiveness.get("effectiveness_deltas") else "none", "response_effectiveness_checksum": effectiveness.get("response_effectiveness_checksum", "")}
