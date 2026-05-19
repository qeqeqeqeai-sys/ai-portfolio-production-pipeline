"""Tier 3I Phase 1C deterministic transmission intelligence summary."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

SCORING_VERSION = "3I.1C.v1"

TOP_K = 5
WEAK_LINK_SCORE_THRESHOLD = 0.45
EMERGING_DRIVER_INFLUENCE_THRESHOLD = 0.70
EMERGING_DRIVER_EDGE_COUNT_THRESHOLD = 2


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_band(value: Any) -> str:
    band = str(value or "").lower()
    return band if band in {"high", "medium", "low"} else "low"


def _edge_sort_key(edge: Dict[str, Any]) -> tuple:
    return (
        -_to_float(edge.get("edge_quality_score"), 0.0),
        str(edge.get("source_node_id", "")),
        str(edge.get("target_node_id", "")),
    )


def _node_sort_key(node: Dict[str, Any]) -> tuple:
    return (-_to_float(node.get("structural_influence_score"), 0.0), str(node.get("node_id", "")))


def build_intelligence_summary(
    quality_scored_edges: Iterable[Dict[str, Any]],
    structural_influence_nodes: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    edges = [dict(edge) for edge in quality_scored_edges]
    nodes = [dict(node) for node in structural_influence_nodes]

    sorted_edges = sorted(edges, key=_edge_sort_key)
    sorted_nodes = sorted(nodes, key=_node_sort_key)

    top_edges = sorted_edges[:TOP_K]
    top_nodes = sorted_nodes[:TOP_K]

    suppressed_edges = [edge for edge in sorted_edges if bool(edge.get("suppressed_for_propagation", False))]

    weak_transmission_links = [
        edge
        for edge in sorted_edges
        if _to_float(edge.get("edge_quality_score"), 0.0) < WEAK_LINK_SCORE_THRESHOLD
        or _safe_band(edge.get("confidence_band")) == "low"
    ]

    emerging_structural_drivers = [
        node
        for node in sorted_nodes
        if _to_float(node.get("structural_influence_score"), 0.0) >= EMERGING_DRIVER_INFLUENCE_THRESHOLD
        and int(_to_float(node.get("contributing_edge_count"), 0.0)) <= EMERGING_DRIVER_EDGE_COUNT_THRESHOLD
    ]

    edge_avg = sum(_to_float(edge.get("edge_quality_score"), 0.0) for edge in edges) / len(edges) if edges else 0.0
    node_avg = (
        sum(_to_float(node.get("structural_influence_score"), 0.0) for node in nodes) / len(nodes) if nodes else 0.0
    )

    high_confidence_edge_count = sum(1 for edge in edges if _safe_band(edge.get("confidence_band")) == "high")
    medium_confidence_edge_count = sum(1 for edge in edges if _safe_band(edge.get("confidence_band")) == "medium")
    low_confidence_edge_count = sum(1 for edge in edges if _safe_band(edge.get("confidence_band")) == "low")

    suppressed_edge_count = len(suppressed_edges)
    suppressed_ratio = (suppressed_edge_count / len(edges)) if edges else 0.0

    high_influence_node_count = sum(
        1 for node in nodes if _safe_band(node.get("influence_confidence_band")) == "high"
    )
    medium_influence_node_count = sum(
        1 for node in nodes if _safe_band(node.get("influence_confidence_band")) == "medium"
    )
    low_influence_node_count = sum(
        1 for node in nodes if _safe_band(node.get("influence_confidence_band")) == "low"
    )

    if edge_avg >= 0.70 and suppressed_ratio < 0.20:
        graph_signal_health_band = "healthy"
    elif edge_avg >= 0.45:
        graph_signal_health_band = "watch"
    else:
        graph_signal_health_band = "fragile"

    graph_signal_health = {
        "average_edge_quality_score": round(edge_avg, 6),
        "average_structural_influence_score": round(node_avg, 6),
        "high_confidence_edge_count": high_confidence_edge_count,
        "medium_confidence_edge_count": medium_confidence_edge_count,
        "low_confidence_edge_count": low_confidence_edge_count,
        "suppressed_edge_count": suppressed_edge_count,
        "high_influence_node_count": high_influence_node_count,
        "medium_influence_node_count": medium_influence_node_count,
        "low_influence_node_count": low_influence_node_count,
        "graph_signal_health_band": graph_signal_health_band,
    }

    rationales: List[str] = []
    for edge in top_edges:
        rationales.append(
            "Top edge ranked by quality score "
            f"{_to_float(edge.get('edge_quality_score'), 0.0):.3f}: "
            f"{edge.get('source_node_id', 'unknown')}->{edge.get('target_node_id', 'unknown')}."
        )
    for node in top_nodes:
        rationales.append(
            "Top node ranked by structural influence score "
            f"{_to_float(node.get('structural_influence_score'), 0.0):.3f}: "
            f"{node.get('node_id', 'unknown')}."
        )

    rationales.append(
        "Graph health classified as "
        f"{graph_signal_health_band} (avg_edge_quality={edge_avg:.3f}, suppressed_ratio={suppressed_ratio:.3f})."
    )

    if suppressed_edges:
        rationales.append(f"Warning: {suppressed_edge_count} edges are suppressed for propagation.")
    if emerging_structural_drivers:
        rationales.append(
            f"Warning: {len(emerging_structural_drivers)} emerging structural drivers show high influence with low edge support."
        )

    return {
        "tier": "3I",
        "phase": "1C",
        "scoring_version": SCORING_VERSION,
        "edges_scored": len(edges),
        "nodes_scored": len(nodes),
        "top_quality_edges": top_edges,
        "top_structural_influence_nodes": top_nodes,
        "suppressed_edges": suppressed_edges,
        "weak_transmission_links": weak_transmission_links,
        "emerging_structural_drivers": emerging_structural_drivers,
        "graph_signal_health": graph_signal_health,
        "explainability_rationales": rationales,
        "status": "success",
    }


def _sample_quality_edges() -> List[Dict[str, Any]]:
    return [
        {"source_node_id": "a", "target_node_id": "b", "edge_quality_score": 0.86, "confidence_band": "high"},
        {
            "source_node_id": "c",
            "target_node_id": "d",
            "edge_quality_score": 0.22,
            "confidence_band": "low",
            "suppressed_for_propagation": True,
        },
    ]


def _sample_structural_nodes() -> List[Dict[str, Any]]:
    return [
        {
            "node_id": "a",
            "structural_influence_score": 0.77,
            "influence_confidence_band": "high",
            "contributing_edge_count": 2,
        },
        {
            "node_id": "d",
            "structural_influence_score": 0.31,
            "influence_confidence_band": "low",
            "contributing_edge_count": 3,
        },
    ]


def main() -> None:
    summary = build_intelligence_summary(_sample_quality_edges(), _sample_structural_nodes())
    output_path = Path("logs/tier3i_transmission_intelligence_summary.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(
        "[tier3i] "
        f"edges_scored={summary['edges_scored']} "
        f"nodes_scored={summary['nodes_scored']} "
        f"graph_signal_health={summary['graph_signal_health']['graph_signal_health_band']} "
        f"status={summary['status']}"
    )


if __name__ == "__main__":
    main()
