"""Tier 4C deterministic bounded attribution metrics."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List

from .structural_simulation import clamp_normalized_score


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _scores(entries: Iterable[Dict[str, Any]]) -> List[float]:
    return [clamp_normalized_score(_to_float(e.get("influence_score", 0.0))) for e in entries]


def compute_attribution_metrics(node_entries: Iterable[Dict[str, Any]], corridor_entries: Iterable[Dict[str, Any]], causal_depth: int, attribution_shift_detected: bool) -> Dict[str, float]:
    nodes = list(node_entries)
    corridors = list(corridor_entries)
    node_scores = sorted(_scores(nodes), reverse=True)
    corridor_scores = sorted(_scores(corridors), reverse=True)
    total_node = sum(node_scores)
    total_corridor = sum(corridor_scores)
    top_share = (node_scores[0] / total_node) if total_node > 0 and node_scores else 0.0
    chokepoint_share = (
        sum(clamp_normalized_score(_to_float(n.get("overload_contribution", 0.0))) for n in nodes) / max(1, len(nodes))
    )
    suppression_effectiveness = (
        sum(clamp_normalized_score(_to_float(c.get("suppression_contribution", 0.0))) for c in corridors) / max(1, len(corridors))
    )
    cascade_score = (
        sum(clamp_normalized_score(_to_float(c.get("cascade_contribution", 0.0))) for c in corridors) / max(1, len(corridors))
    )
    depth_score = clamp_normalized_score(causal_depth / 6.0)
    stability_score = clamp_normalized_score(1.0 - abs((total_node / max(1, len(node_scores))) - (total_corridor / max(1, len(corridor_scores)))))
    shift_score = 1.0 if attribution_shift_detected else 0.0
    return {
        "influence_concentration_score": clamp_normalized_score(top_share),
        "chokepoint_attribution_score": clamp_normalized_score(chokepoint_share),
        "suppression_effectiveness_score": clamp_normalized_score(suppression_effectiveness),
        "cascade_attribution_score": clamp_normalized_score(cascade_score),
        "causal_depth_score": depth_score,
        "lineage_stability_score": stability_score,
        "attribution_shift_score": shift_score,
    }
