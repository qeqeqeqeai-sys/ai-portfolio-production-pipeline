"""Tier 4C deterministic influence attribution."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List

from .structural_simulation import clamp_normalized_score
from .topology_hashing import normalize_for_replay


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _stable_reason(parts: Iterable[str]) -> str:
    entries = sorted({str(p) for p in parts if str(p).strip()})
    return "; ".join(entries)


def attribute_node_influence(node_metrics: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for node in sorted(node_metrics, key=lambda n: str(n.get("node_id", ""))):
        node_id = str(node.get("node_id", ""))
        stress_contribution = clamp_normalized_score(_to_float(node.get("propagated_stress", node.get("stress", 0.0))))
        overload_contribution = clamp_normalized_score(_to_float(node.get("overload", node.get("chokepoint_score", 0.0))))
        resilience_contribution = clamp_normalized_score(_to_float(node.get("resilience_degradation", node.get("fragility", 0.0))))
        suppression_contribution = clamp_normalized_score(_to_float(node.get("suppression", 0.0)))
        cascade_contribution = clamp_normalized_score(_to_float(node.get("cascade", _to_float(node.get("is_overloaded", 0.0)))))
        influence_score = clamp_normalized_score(
            0.30 * stress_contribution
            + 0.22 * overload_contribution
            + 0.18 * resilience_contribution
            + 0.15 * suppression_contribution
            + 0.15 * cascade_contribution
        )
        reasons = []
        if stress_contribution >= 0.55:
            reasons.append("high propagated stress")
        if overload_contribution >= 0.55:
            reasons.append("high chokepoint load")
        if resilience_contribution >= 0.55:
            reasons.append("resilience degradation exposure")
        if suppression_contribution >= 0.40:
            reasons.append("suppression interaction")
        if cascade_contribution >= 0.40:
            reasons.append("cascade involvement")
        rows.append(
            {
                "node_id": node_id,
                "influence_score": influence_score,
                "stress_contribution": stress_contribution,
                "overload_contribution": overload_contribution,
                "resilience_contribution": resilience_contribution,
                "suppression_contribution": suppression_contribution,
                "cascade_contribution": cascade_contribution,
                "attribution_reason": _stable_reason(reasons) or "baseline structural contribution",
            }
        )

    ranked = sorted(rows, key=lambda r: (-r["influence_score"], r["node_id"]))
    for index, row in enumerate(ranked, start=1):
        row["attribution_rank"] = index
    return normalize_for_replay(ranked)


def attribute_corridor_influence(corridor_metrics: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for corridor in sorted(corridor_metrics, key=lambda c: (str(c.get("source_node_id", "")), str(c.get("target_node_id", "")))):
        source = str(corridor.get("source_node_id", ""))
        target = str(corridor.get("target_node_id", ""))
        corridor_id = str(corridor.get("corridor_id", f"{source}->{target}"))
        stress_contribution = clamp_normalized_score(_to_float(corridor.get("stress", corridor.get("propagated_stress", 0.0))))
        overload_contribution = clamp_normalized_score(_to_float(corridor.get("downstream_overload", 0.0)))
        resilience_contribution = clamp_normalized_score(_to_float(corridor.get("resilience_impact", 0.0)))
        suppression_contribution = clamp_normalized_score(_to_float(corridor.get("suppression", 1.0 if corridor.get("suppressed_for_propagation", False) else 0.0)))
        cascade_contribution = clamp_normalized_score(_to_float(corridor.get("cascade", 1.0 if str(corridor.get("state", "")) == "failed" else 0.0)))
        deterioration = clamp_normalized_score(_to_float(corridor.get("deterioration", 1.0 - _to_float(corridor.get("edge_quality_score", 1.0)))))
        influence_score = clamp_normalized_score(
            0.26 * stress_contribution
            + 0.22 * overload_contribution
            + 0.16 * resilience_contribution
            + 0.16 * cascade_contribution
            + 0.12 * deterioration
            - 0.08 * suppression_contribution
        )
        reasons = []
        if deterioration >= 0.40:
            reasons.append("deteriorated corridor state")
        if overload_contribution >= 0.50:
            reasons.append("downstream overload pressure")
        if cascade_contribution >= 0.50:
            reasons.append("failure cascade linkage")
        if suppression_contribution >= 0.60:
            reasons.append("suppression reduced propagation")
        rows.append(
            {
                "corridor_id": corridor_id,
                "source_node_id": source,
                "target_node_id": target,
                "influence_score": influence_score,
                "stress_contribution": stress_contribution,
                "overload_contribution": overload_contribution,
                "resilience_contribution": resilience_contribution,
                "suppression_contribution": suppression_contribution,
                "cascade_contribution": cascade_contribution,
                "attribution_reason": _stable_reason(reasons) or "baseline corridor contribution",
            }
        )
    ranked = sorted(rows, key=lambda r: (-r["influence_score"], r["corridor_id"]))
    for index, row in enumerate(ranked, start=1):
        row["attribution_rank"] = index
    return normalize_for_replay(ranked)


def compute_structural_influence_summary(node_metrics: Iterable[Dict[str, Any]], corridor_metrics: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    node_attribution = attribute_node_influence(node_metrics)
    corridor_attribution = attribute_corridor_influence(corridor_metrics)
    dominant_node = node_attribution[0]["node_id"] if node_attribution else ""
    dominant_corridor = corridor_attribution[0]["corridor_id"] if corridor_attribution else ""
    return normalize_for_replay(
        {
            "node_attribution": node_attribution,
            "corridor_attribution": corridor_attribution,
            "operational_diagnostics": {
                "attribution_entries": len(node_attribution) + len(corridor_attribution),
                "dominant_influence_node": dominant_node,
                "dominant_influence_corridor": dominant_corridor,
            },
        }
    )
