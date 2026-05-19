"""Tier 3I Phase 2A deterministic multi-hop propagation quality scoring."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

SCORING_VERSION = "3I.2A.v1"

HIGH_CONFIDENCE_THRESHOLD = 0.75
MEDIUM_CONFIDENCE_THRESHOLD = 0.45
SUPPRESSION_THRESHOLD = 0.30

MAX_REINFORCEMENT = 0.15
CONTAMINATION_PENALTY_THRESHOLD = 0.25

HOP_DECAY_BY_COUNT = {
    1: 1.0,
    2: 0.75,
    3: 0.55,
}

SUPPRESSED_EDGE_PENALTY = 0.35
LOW_CONFIDENCE_EDGE_PENALTY = 0.08


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _confidence_band(score: float) -> str:
    if score >= HIGH_CONFIDENCE_THRESHOLD:
        return "high"
    if score >= MEDIUM_CONFIDENCE_THRESHOLD:
        return "medium"
    return "low"


def _edge_sort_key(edge: Dict[str, Any]) -> Tuple[str, str, float]:
    return (
        str(edge.get("source_node_id", "")),
        str(edge.get("target_node_id", "")),
        -_to_float(edge.get("edge_quality_score"), 0.0),
    )


def _path_sort_key(path: Dict[str, Any]) -> Tuple[str, str, Tuple[str, ...]]:
    return (
        str(path.get("source_node_id", "")),
        str(path.get("terminal_node_id", "")),
        tuple(str(n) for n in path.get("path_nodes", [])),
    )


def _build_adjacency(edges: Sequence[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    adjacency: Dict[str, List[Dict[str, Any]]] = {}
    for edge in sorted(edges, key=_edge_sort_key):
        source = str(edge.get("source_node_id", ""))
        adjacency.setdefault(source, []).append(edge)
    return adjacency


def _path_id(path_nodes: Sequence[str]) -> str:
    return "path::" + "->".join(path_nodes)


def _compute_reinforcement(path_edges: Sequence[Dict[str, Any]]) -> float:
    if len(path_edges) < 2:
        return 0.0

    pair_scores: List[float] = []
    for idx in range(len(path_edges) - 1):
        left = path_edges[idx]
        right = path_edges[idx + 1]

        recurrence_avg = (
            _to_float(left.get("recurrence_score"), 0.0) + _to_float(right.get("recurrence_score"), 0.0)
        ) / 2.0
        persistence_avg = (
            _to_float(left.get("persistence_score"), 0.0) + _to_float(right.get("persistence_score"), 0.0)
        ) / 2.0
        evidence_avg = (
            _to_float(left.get("evidence_strength_score"), 0.0)
            + _to_float(right.get("evidence_strength_score"), 0.0)
        ) / 2.0

        pair_strength = _clip01((0.45 * recurrence_avg) + (0.35 * persistence_avg) + (0.20 * evidence_avg))
        pair_scores.append(pair_strength)

    if not pair_scores:
        return 0.0

    return _clip01(sum(pair_scores) / len(pair_scores)) * MAX_REINFORCEMENT


def _compute_penalty(path_edges: Sequence[Dict[str, Any]]) -> Tuple[float, Dict[str, float], List[str]]:
    ambiguity = sum(_to_float(edge.get("ambiguity_penalty"), 0.0) for edge in path_edges) / max(len(path_edges), 1)
    conflict = sum(_to_float(edge.get("conflict_penalty"), 0.0) for edge in path_edges) / max(len(path_edges), 1)

    suppressed_count = sum(1 for edge in path_edges if bool(edge.get("suppressed_for_propagation", False)))
    low_conf_count = sum(1 for edge in path_edges if str(edge.get("confidence_band", "")).lower() == "low")

    suppression_penalty = SUPPRESSED_EDGE_PENALTY if suppressed_count else 0.0
    low_conf_penalty = min(LOW_CONFIDENCE_EDGE_PENALTY * low_conf_count, 0.24)

    total_penalty = _clip01((0.5 * ambiguity) + (0.5 * conflict) + suppression_penalty + low_conf_penalty)

    warnings: List[str] = []
    if suppressed_count:
        warnings.append("contains_suppressed_edge")
    if low_conf_count:
        warnings.append("contains_low_confidence_edge")
    if (ambiguity + conflict) > CONTAMINATION_PENALTY_THRESHOLD:
        warnings.append("high_ambiguity_conflict_accumulation")

    return total_penalty, {
        "ambiguity_component": round(ambiguity, 6),
        "conflict_component": round(conflict, 6),
        "suppression_component": round(suppression_penalty, 6),
        "low_confidence_component": round(low_conf_penalty, 6),
    }, warnings


def score_multi_hop_paths(
    quality_scored_edges: Iterable[Dict[str, Any]],
    max_hops: int = 3,
) -> List[Dict[str, Any]]:
    """Build deterministic, bounded multi-hop path quality scores."""
    bounded_hops = max(1, min(3, int(max_hops)))
    edges = [dict(edge) for edge in quality_scored_edges]
    adjacency = _build_adjacency(edges)

    paths: List[Dict[str, Any]] = []

    for source_node in sorted(adjacency.keys()):
        stack: List[Tuple[str, List[str], List[Dict[str, Any]]]] = [(source_node, [source_node], [])]

        while stack:
            current_node, path_nodes, path_edges = stack.pop()

            if path_edges:
                hop_count = len(path_edges)
                hop_decay_factor = HOP_DECAY_BY_COUNT.get(hop_count, 0.55)
                avg_edge_quality = sum(_to_float(edge.get("edge_quality_score"), 0.0) for edge in path_edges) / hop_count
                reinforcement_score = _compute_reinforcement(path_edges)
                accumulated_penalty, penalty_components, penalty_warnings = _compute_penalty(path_edges)

                raw_score = (avg_edge_quality * hop_decay_factor) + reinforcement_score - accumulated_penalty
                path_quality_score = _clip01(raw_score)

                has_suppressed_edge = any(bool(edge.get("suppressed_for_propagation", False)) for edge in path_edges)
                confidence_band = _confidence_band(path_quality_score)
                suppressed_for_propagation = path_quality_score < SUPPRESSION_THRESHOLD or has_suppressed_edge
                contamination_warning = bool(penalty_warnings) or accumulated_penalty > CONTAMINATION_PENALTY_THRESHOLD

                warning_flags = list(penalty_warnings)
                if suppressed_for_propagation:
                    warning_flags.append("suppressed_for_propagation")
                if confidence_band == "low":
                    warning_flags.append("low_path_confidence")

                record = {
                    "path_id": _path_id(path_nodes),
                    "source_node_id": source_node,
                    "terminal_node_id": current_node,
                    "path_nodes": list(path_nodes),
                    "path_edges": [dict(edge) for edge in path_edges],
                    "hop_count": hop_count,
                    "path_quality_score": round(path_quality_score, 6),
                    "hop_decay_factor": hop_decay_factor,
                    "reinforcement_score": round(reinforcement_score, 6),
                    "path_confidence_band": confidence_band,
                    "suppressed_for_propagation": suppressed_for_propagation,
                    "cycle_suppressed": False,
                    "contamination_warning": contamination_warning,
                    "explainability_payload": {
                        "component_scores": {
                            "average_edge_quality": round(avg_edge_quality, 6),
                            "hop_decay_factor": round(hop_decay_factor, 6),
                            "reinforcement_score": round(reinforcement_score, 6),
                            "accumulated_penalty": round(accumulated_penalty, 6),
                        },
                        "edge_sequence": [
                            f"{edge.get('source_node_id', 'unknown')}->{edge.get('target_node_id', 'unknown')}"
                            for edge in path_edges
                        ],
                        "penalty_components": penalty_components,
                        "rationale": {
                            "hop_decay_rationale": f"Applied deterministic hop decay for {hop_count}-hop path.",
                            "reinforcement_rationale": "Reinforcement derived from adjacent recurrence/persistence/evidence alignment.",
                            "penalty_rationale": "Penalty accumulates ambiguity, conflict, suppression, and low-confidence risk.",
                        },
                        "warnings": sorted(set(warning_flags)),
                    },
                    "scoring_version": SCORING_VERSION,
                }
                paths.append(record)

            if len(path_edges) >= bounded_hops:
                continue

            for edge in reversed(adjacency.get(current_node, [])):
                target = str(edge.get("target_node_id", ""))
                if not target:
                    continue
                if target in path_nodes:
                    continue
                stack.append((target, path_nodes + [target], path_edges + [edge]))

    return sorted(paths, key=_path_sort_key)


def build_summary(paths: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    high = sum(1 for p in paths if p.get("path_confidence_band") == "high")
    medium = sum(1 for p in paths if p.get("path_confidence_band") == "medium")
    low = sum(1 for p in paths if p.get("path_confidence_band") == "low")

    suppressed = sum(1 for p in paths if bool(p.get("suppressed_for_propagation", False)))
    cycle_suppressed = sum(1 for p in paths if bool(p.get("cycle_suppressed", False)))
    contamination = sum(1 for p in paths if bool(p.get("contamination_warning", False)))

    top_paths = sorted(paths, key=lambda p: _to_float(p.get("path_quality_score"), 0.0), reverse=True)[:5]

    return {
        "tier": "3I",
        "phase": "2A",
        "scoring_version": SCORING_VERSION,
        "paths_scored": len(paths),
        "high_confidence_paths": high,
        "medium_confidence_paths": medium,
        "low_confidence_paths": low,
        "suppressed_paths": suppressed,
        "cycle_suppressed_paths": cycle_suppressed,
        "contamination_warnings": contamination,
        "top_paths": top_paths,
        "status": "success",
    }


def _sample_quality_edges() -> List[Dict[str, Any]]:
    return [
        {
            "source_node_id": "a",
            "target_node_id": "b",
            "edge_quality_score": 0.82,
            "decay_adjusted_weight": 0.82,
            "confidence_band": "high",
            "suppressed_for_propagation": False,
            "recurrence_score": 0.80,
            "persistence_score": 0.72,
            "evidence_strength_score": 0.84,
            "ambiguity_penalty": 0.02,
            "conflict_penalty": 0.01,
            "metadata": {"sample": True},
        },
        {
            "source_node_id": "b",
            "target_node_id": "c",
            "edge_quality_score": 0.78,
            "decay_adjusted_weight": 0.78,
            "confidence_band": "high",
            "suppressed_for_propagation": False,
            "recurrence_score": 0.75,
            "persistence_score": 0.71,
            "evidence_strength_score": 0.80,
            "ambiguity_penalty": 0.03,
            "conflict_penalty": 0.02,
            "metadata": {"sample": True},
        },
        {
            "source_node_id": "c",
            "target_node_id": "d",
            "edge_quality_score": 0.55,
            "decay_adjusted_weight": 0.55,
            "confidence_band": "medium",
            "suppressed_for_propagation": False,
            "recurrence_score": 0.40,
            "persistence_score": 0.46,
            "evidence_strength_score": 0.57,
            "ambiguity_penalty": 0.08,
            "conflict_penalty": 0.06,
            "metadata": {"sample": True},
        },
    ]


def main() -> None:
    paths = score_multi_hop_paths(_sample_quality_edges())
    summary = build_summary(paths)

    output_path = Path("logs/tier3i_multi_hop_quality_summary.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(
        "[tier3i] "
        f"paths_scored={summary['paths_scored']} "
        f"high_confidence_paths={summary['high_confidence_paths']} "
        f"suppressed_paths={summary['suppressed_paths']} "
        f"status={summary['status']}"
    )


if __name__ == "__main__":
    main()
