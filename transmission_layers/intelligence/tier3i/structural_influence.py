"""Tier 3I Phase 1B deterministic structural influence scoring."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple

SCORING_VERSION = "3I.1B.v1"

SUPPRESSED_EDGE_FACTOR = 0.10
DIRECT_INFLUENCE_WEIGHT = 0.40
DOWNSTREAM_REACH_WEIGHT = 0.20
WEIGHTED_CENTRALITY_WEIGHT = 0.25
PERSISTENCE_ADJUSTED_WEIGHT = 0.15

HIGH_CONFIDENCE_THRESHOLD = 0.75
MEDIUM_CONFIDENCE_THRESHOLD = 0.45

LOW_EDGE_COUNT_WARNING_THRESHOLD = 2


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _confidence_band(score: float) -> str:
    if score >= HIGH_CONFIDENCE_THRESHOLD:
        return "high"
    if score >= MEDIUM_CONFIDENCE_THRESHOLD:
        return "medium"
    return "low"


def _edge_strength(edge: Dict[str, Any]) -> float:
    quality = edge.get("edge_quality_score")
    if quality is None:
        quality = edge.get("decay_adjusted_weight", edge.get("base_weight", 0.5))
    quality_score = _clip01(_to_float(quality, default=0.5))

    decay_weight = _clip01(_to_float(edge.get("decay_adjusted_weight", quality_score), default=quality_score))
    recurrence = _clip01(_to_float(edge.get("recurrence_score", 0.5), default=0.5))
    evidence = _clip01(_to_float(edge.get("evidence_strength_score", quality_score), default=quality_score))

    strength = (0.50 * quality_score) + (0.20 * decay_weight) + (0.15 * recurrence) + (0.15 * evidence)
    if edge.get("suppressed_for_propagation", False):
        strength *= SUPPRESSED_EDGE_FACTOR
    return _clip01(strength)


def score_structural_influence(edges: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    edge_list = [dict(edge) for edge in edges]
    if not edge_list:
        return []

    node_ids: Set[str] = set()
    for edge in edge_list:
        source = str(edge.get("source_node_id", ""))
        target = str(edge.get("target_node_id", ""))
        if source:
            node_ids.add(source)
        if target:
            node_ids.add(target)

    outgoing_mass: Dict[str, float] = {node_id: 0.0 for node_id in node_ids}
    incoming_mass: Dict[str, float] = {node_id: 0.0 for node_id in node_ids}
    downstream_targets: Dict[str, Set[str]] = {node_id: set() for node_id in node_ids}
    persistence_values: Dict[str, List[float]] = {node_id: [] for node_id in node_ids}
    node_edge_pairs: Dict[str, List[str]] = {node_id: [] for node_id in node_ids}
    node_edge_counts: Dict[str, int] = {node_id: 0 for node_id in node_ids}
    node_high_conf_counts: Dict[str, int] = {node_id: 0 for node_id in node_ids}
    node_suppressed_counts: Dict[str, int] = {node_id: 0 for node_id in node_ids}

    for edge in edge_list:
        source = str(edge.get("source_node_id", ""))
        target = str(edge.get("target_node_id", ""))
        if not source or not target:
            continue

        strength = _edge_strength(edge)
        outgoing_mass[source] += strength
        incoming_mass[target] += strength
        downstream_targets[source].add(target)

        persistence_val = _clip01(_to_float(edge.get("persistence_score", 0.5), default=0.5))
        persistence_values[source].append(persistence_val)
        persistence_values[target].append(persistence_val)

        pair = f"{source}->{target}"
        node_edge_pairs[source].append(pair)
        node_edge_pairs[target].append(pair)

        for node_id in (source, target):
            node_edge_counts[node_id] += 1
            if edge.get("confidence_band") == "high":
                node_high_conf_counts[node_id] += 1
            if edge.get("suppressed_for_propagation", False):
                node_suppressed_counts[node_id] += 1

    results: List[Dict[str, Any]] = []
    for node_id in sorted(node_ids):
        outgoing = outgoing_mass[node_id]
        direct_influence = _clip01(outgoing / (outgoing + 1.0))
        reach_count = len(downstream_targets[node_id])
        reach = _clip01(reach_count / (reach_count + 2.0))
        centrality_mass = outgoing_mass[node_id] + incoming_mass[node_id]
        weighted_centrality = _clip01(centrality_mass / (centrality_mass + 1.0))

        avg_persistence = (
            sum(persistence_values[node_id]) / len(persistence_values[node_id])
            if persistence_values[node_id]
            else 0.5
        )
        persistence_adjusted = _clip01((0.75 * direct_influence) + (0.25 * avg_persistence))

        structural_score = _clip01(
            (DIRECT_INFLUENCE_WEIGHT * direct_influence)
            + (DOWNSTREAM_REACH_WEIGHT * reach)
            + (WEIGHTED_CENTRALITY_WEIGHT * weighted_centrality)
            + (PERSISTENCE_ADJUSTED_WEIGHT * persistence_adjusted)
        )

        warnings: List[str] = []
        if node_edge_counts[node_id] < LOW_EDGE_COUNT_WARNING_THRESHOLD:
            warnings.append("Influence estimate based on low contributing edge count.")
        if node_suppressed_counts[node_id] > 0:
            warnings.append("Suppressed edges were heavily downweighted in influence scoring.")

        rationale = [
            "Direct influence is based on quality-adjusted outgoing strength.",
            "Downstream reach rewards distinct connected targets.",
            "Weighted centrality blends incoming and outgoing edge mass.",
            "Persistence-adjusted influence boosts sustained relationships.",
        ]
        rationale.extend(warnings)

        results.append(
            {
                "node_id": node_id,
                "direct_influence_score": round(direct_influence, 6),
                "downstream_reach_score": round(reach, 6),
                "weighted_centrality_score": round(weighted_centrality, 6),
                "persistence_adjusted_influence_score": round(persistence_adjusted, 6),
                "structural_influence_score": round(structural_score, 6),
                "structural_importance_rank": 0,
                "influence_confidence_band": _confidence_band(structural_score),
                "contributing_edge_count": node_edge_counts[node_id],
                "high_confidence_edge_count": node_high_conf_counts[node_id],
                "suppressed_edge_count": node_suppressed_counts[node_id],
                "explainability_payload": {
                    "component_scores": {
                        "direct_influence_score": round(direct_influence, 6),
                        "downstream_reach_score": round(reach, 6),
                        "weighted_centrality_score": round(weighted_centrality, 6),
                        "persistence_adjusted_influence_score": round(persistence_adjusted, 6),
                    },
                    "contributing_edges": sorted(set(node_edge_pairs[node_id])),
                    "rationale": rationale,
                    "warnings": warnings,
                },
                "scoring_version": SCORING_VERSION,
            }
        )

    ranked = sorted(
        results,
        key=lambda row: (-row["structural_influence_score"], row["node_id"]),
    )
    for idx, row in enumerate(ranked, start=1):
        row["structural_importance_rank"] = idx

    return ranked


def _sample_scored_edges() -> List[Dict[str, Any]]:
    return [
        {
            "source_node_id": "alpha",
            "target_node_id": "beta",
            "edge_quality_score": 0.9,
            "decay_adjusted_weight": 0.85,
            "confidence_band": "high",
            "suppressed_for_propagation": False,
            "recurrence_score": 0.8,
            "persistence_score": 0.7,
            "evidence_strength_score": 0.9,
        },
        {
            "source_node_id": "alpha",
            "target_node_id": "gamma",
            "edge_quality_score": 0.8,
            "decay_adjusted_weight": 0.8,
            "confidence_band": "high",
            "suppressed_for_propagation": False,
            "recurrence_score": 0.7,
            "persistence_score": 0.8,
            "evidence_strength_score": 0.85,
        },
        {
            "source_node_id": "delta",
            "target_node_id": "gamma",
            "edge_quality_score": 0.2,
            "decay_adjusted_weight": 0.3,
            "confidence_band": "low",
            "suppressed_for_propagation": True,
            "recurrence_score": 0.2,
            "persistence_score": 0.2,
            "evidence_strength_score": 0.2,
        },
    ]


def build_summary(node_scores: List[Dict[str, Any]]) -> Dict[str, Any]:
    high = sum(1 for row in node_scores if row["influence_confidence_band"] == "high")
    medium = sum(1 for row in node_scores if row["influence_confidence_band"] == "medium")
    low = sum(1 for row in node_scores if row["influence_confidence_band"] == "low")
    top_nodes = [row["node_id"] for row in node_scores[:5]]

    return {
        "tier": "3I",
        "phase": "1B",
        "scoring_version": SCORING_VERSION,
        "nodes_scored": len(node_scores),
        "high_influence_nodes": high,
        "medium_influence_nodes": medium,
        "low_influence_nodes": low,
        "top_nodes": top_nodes,
        "status": "success",
    }


def main() -> None:
    node_scores = score_structural_influence(_sample_scored_edges())
    summary = build_summary(node_scores)
    output_path = Path("logs/tier3i_structural_influence_summary.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    top_node = node_scores[0]["node_id"] if node_scores else "none"
    print(
        "[tier3i] "
        f"nodes_scored={summary['nodes_scored']} "
        f"top_node={top_node} "
        f"status={summary['status']}"
    )


if __name__ == "__main__":
    main()
