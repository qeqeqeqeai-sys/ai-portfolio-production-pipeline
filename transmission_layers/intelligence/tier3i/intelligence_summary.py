"""Tier 3I Phase 2C deterministic transmission intelligence summary integration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

SCORING_VERSION = "3I.2C.v1"

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


def _path_sort_key(path: Dict[str, Any]) -> tuple:
    return (
        -_to_float(path.get("path_quality_score"), 0.0),
        str(path.get("source_node_id", "")),
        str(path.get("terminal_node_id", "")),
        str(path.get("path_id", "")),
    )


def _path_id_sort_key(item: Dict[str, Any]) -> tuple:
    return (str(item.get("path_id", "")),)


def _explanation_priority(record: Dict[str, Any]) -> tuple:
    priority = {
        "actionable_watchlist": 0,
        "weak_signal": 1,
        "suppressed_noise": 2,
        "contaminated_chain": 3,
    }
    label = str(record.get("decision_usefulness_label", ""))
    return (priority.get(label, 99), str(record.get("path_id", "")))


def build_intelligence_summary(
    quality_scored_edges: Iterable[Dict[str, Any]],
    structural_influence_nodes: Iterable[Dict[str, Any]],
    multi_hop_paths: Iterable[Dict[str, Any]] | None = None,
    path_explanations: Iterable[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    edges = [dict(edge) for edge in quality_scored_edges]
    nodes = [dict(node) for node in structural_influence_nodes]
    paths = [dict(path) for path in (multi_hop_paths or [])]
    explanations = [dict(explanation) for explanation in (path_explanations or [])]

    sorted_edges = sorted(edges, key=_edge_sort_key)
    sorted_nodes = sorted(nodes, key=_node_sort_key)
    sorted_paths = sorted(paths, key=_path_sort_key)

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

    top_multi_hop_paths = sorted_paths[:TOP_K]
    actionable_causal_chains = sorted(
        [record for record in explanations if str(record.get("decision_usefulness_label", "")) == "actionable_watchlist"],
        key=_explanation_priority,
    )[:TOP_K]
    suppressed_paths = sorted(
        [path for path in paths if bool(path.get("suppressed_for_propagation", False))],
        key=_path_id_sort_key,
    )
    contaminated_paths = sorted(
        [path for path in paths if bool(path.get("contamination_warning", False))],
        key=_path_id_sort_key,
    )
    weak_causal_chains = sorted(
        [record for record in explanations if str(record.get("decision_usefulness_label", "")) == "weak_signal"],
        key=_explanation_priority,
    )

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

    path_avg = sum(_to_float(path.get("path_quality_score"), 0.0) for path in paths) / len(paths) if paths else 0.0
    high_confidence_path_count = sum(1 for path in paths if _safe_band(path.get("path_confidence_band")) == "high")
    medium_confidence_path_count = sum(1 for path in paths if _safe_band(path.get("path_confidence_band")) == "medium")
    low_confidence_path_count = sum(1 for path in paths if _safe_band(path.get("path_confidence_band")) == "low")
    suppressed_path_count = len(suppressed_paths)
    contaminated_path_count = len(contaminated_paths)
    actionable_watchlist_count = len(actionable_causal_chains)
    weak_signal_count = len(weak_causal_chains)

    suppressed_path_ratio = (suppressed_path_count / len(paths)) if paths else 0.0
    contaminated_path_ratio = (contaminated_path_count / len(paths)) if paths else 0.0

    if path_avg >= 0.70 and suppressed_path_ratio < 0.20 and contaminated_path_ratio < 0.20:
        multi_hop_health_band = "healthy"
    elif path_avg >= 0.45:
        multi_hop_health_band = "watch"
    else:
        multi_hop_health_band = "fragile"

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

    multi_hop_signal_health = {
        "average_path_quality_score": round(path_avg, 6),
        "high_confidence_path_count": high_confidence_path_count,
        "medium_confidence_path_count": medium_confidence_path_count,
        "low_confidence_path_count": low_confidence_path_count,
        "suppressed_path_count": suppressed_path_count,
        "contaminated_path_count": contaminated_path_count,
        "actionable_watchlist_count": actionable_watchlist_count,
        "weak_signal_count": weak_signal_count,
        "multi_hop_health_band": multi_hop_health_band,
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
    if top_multi_hop_paths:
        top_path = top_multi_hop_paths[0]
        rationales.append(
            "Top multi-hop path ranked by quality score "
            f"{_to_float(top_path.get('path_quality_score'), 0.0):.3f}: "
            f"{top_path.get('path_id', 'unknown_path')}."
        )

    rationales.append(
        "Graph health classified as "
        f"{graph_signal_health_band} (avg_edge_quality={edge_avg:.3f}, suppressed_ratio={suppressed_ratio:.3f})."
    )
    rationales.append(
        "Multi-hop health classified as "
        f"{multi_hop_health_band} (avg_path_quality={path_avg:.3f}, suppressed_ratio={suppressed_path_ratio:.3f}, "
        f"contaminated_ratio={contaminated_path_ratio:.3f})."
    )

    if suppressed_edges:
        rationales.append(f"Warning: {suppressed_edge_count} edges are suppressed for propagation.")
    if emerging_structural_drivers:
        rationales.append(
            f"Warning: {len(emerging_structural_drivers)} emerging structural drivers show high influence with low edge support."
        )
    if suppressed_paths:
        rationales.append(f"Warning: {suppressed_path_count} multi-hop paths are suppressed for propagation.")
    if contaminated_paths:
        rationales.append(f"Warning: {contaminated_path_count} multi-hop paths carry contamination warnings.")
    if actionable_causal_chains:
        rationales.append(
            f"Actionable causal chains identified: {len(actionable_causal_chains)} watchlist paths passed explainability filters."
        )

    return {
        "tier": "3I",
        "phase": "2C",
        "scoring_version": SCORING_VERSION,
        "edges_scored": len(edges),
        "nodes_scored": len(nodes),
        "paths_scored": len(paths),
        "paths_explained": len(explanations),
        "top_quality_edges": top_edges,
        "top_structural_influence_nodes": top_nodes,
        "top_multi_hop_paths": top_multi_hop_paths,
        "suppressed_edges": suppressed_edges,
        "weak_transmission_links": weak_transmission_links,
        "emerging_structural_drivers": emerging_structural_drivers,
        "actionable_causal_chains": actionable_causal_chains,
        "suppressed_paths": suppressed_paths,
        "contaminated_paths": contaminated_paths,
        "weak_causal_chains": weak_causal_chains,
        "graph_signal_health": graph_signal_health,
        "multi_hop_signal_health": multi_hop_signal_health,
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


def _sample_multi_hop_paths() -> List[Dict[str, Any]]:
    return [
        {
            "path_id": "path::a->b->c",
            "source_node_id": "a",
            "terminal_node_id": "c",
            "path_quality_score": 0.78,
            "path_confidence_band": "high",
            "suppressed_for_propagation": False,
            "contamination_warning": False,
        },
        {
            "path_id": "path::c->d->e",
            "source_node_id": "c",
            "terminal_node_id": "e",
            "path_quality_score": 0.42,
            "path_confidence_band": "low",
            "suppressed_for_propagation": True,
            "contamination_warning": True,
        },
    ]


def _sample_path_explanations() -> List[Dict[str, Any]]:
    return [
        {"path_id": "path::a->b->c", "decision_usefulness_label": "actionable_watchlist"},
        {"path_id": "path::c->d->e", "decision_usefulness_label": "weak_signal"},
    ]


def main() -> None:
    summary = build_intelligence_summary(
        _sample_quality_edges(),
        _sample_structural_nodes(),
        _sample_multi_hop_paths(),
        _sample_path_explanations(),
    )
    output_path = Path("logs/tier3i_transmission_intelligence_summary.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(
        "[tier3i] "
        f"edges_scored={summary['edges_scored']} "
        f"nodes_scored={summary['nodes_scored']} "
        f"paths_scored={summary['paths_scored']} "
        f"graph_signal_health={summary['graph_signal_health']['graph_signal_health_band']} "
        f"multi_hop_health={summary['multi_hop_signal_health']['multi_hop_health_band']} "
        f"status={summary['status']}"
    )


if __name__ == "__main__":
    main()
