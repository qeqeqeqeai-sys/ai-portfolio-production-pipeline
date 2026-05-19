"""Tier 3I Phase 1A deterministic transmission edge quality scoring."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

SCORING_VERSION = "3I.1A.v1"

EVIDENCE_WEIGHT = 0.30
PERSISTENCE_WEIGHT = 0.20
RECURRENCE_WEIGHT = 0.20
DIRECTIONAL_WEIGHT = 0.15
AMBIGUITY_WEIGHT = 0.08
CONFLICT_WEIGHT = 0.05
FRESHNESS_WEIGHT = 0.02

SUPPRESSION_THRESHOLD = 0.30
HIGH_CONFIDENCE_THRESHOLD = 0.75
MEDIUM_CONFIDENCE_THRESHOLD = 0.45

EVIDENCE_COUNT_CAP = 10.0
RECURRENCE_COUNT_CAP = 10.0
PERSISTENCE_DAYS_CAP = 365.0
MAX_AMBIGUITY_COUNT = 5.0
MAX_CONFLICT_COUNT = 5.0
FRESHNESS_DAYS_CAP = 30.0


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


def score_edge_quality(edge: Dict[str, Any]) -> Dict[str, Any]:
    """Score a single edge record deterministically and return enriched output."""
    enriched = dict(edge)

    base_weight = _clip01(_to_float(edge.get("base_weight"), default=0.5))
    evidence_count = _clip01(_to_float(edge.get("evidence_count")) / EVIDENCE_COUNT_CAP)
    evidence_confidence = _clip01(_to_float(edge.get("evidence_confidence"), default=0.5))
    recurrence_score = _clip01(_to_float(edge.get("recurrence_count")) / RECURRENCE_COUNT_CAP)
    persistence_score = _clip01(_to_float(edge.get("persistence_days")) / PERSISTENCE_DAYS_CAP)
    directional_consistency_score = _clip01(
        _to_float(edge.get("directional_consistency"), default=0.5)
    )

    ambiguity_penalty = _clip01(_to_float(edge.get("ambiguity_count")) / MAX_AMBIGUITY_COUNT)
    conflict_penalty = _clip01(_to_float(edge.get("conflict_count")) / MAX_CONFLICT_COUNT)
    freshness_decay_penalty = _clip01(
        _to_float(edge.get("last_seen_days_ago")) / FRESHNESS_DAYS_CAP
    )

    evidence_strength_score = _clip01((0.6 * evidence_count) + (0.4 * evidence_confidence))

    positive_score = (
        (evidence_strength_score * EVIDENCE_WEIGHT)
        + (persistence_score * PERSISTENCE_WEIGHT)
        + (recurrence_score * RECURRENCE_WEIGHT)
        + (directional_consistency_score * DIRECTIONAL_WEIGHT)
    )
    negative_score = (
        (ambiguity_penalty * AMBIGUITY_WEIGHT)
        + (conflict_penalty * CONFLICT_WEIGHT)
        + (freshness_decay_penalty * FRESHNESS_WEIGHT)
    )

    edge_quality_score = _clip01(positive_score - negative_score)
    decay_adjusted_weight = _clip01(base_weight * (1.0 - freshness_decay_penalty))
    confidence_band = _confidence_band(edge_quality_score)
    suppressed_for_propagation = edge_quality_score < SUPPRESSION_THRESHOLD

    explainability_payload = {
        "positive_components": {
            "evidence_strength_score": round(evidence_strength_score, 6),
            "persistence_score": round(persistence_score, 6),
            "recurrence_score": round(recurrence_score, 6),
            "directional_consistency_score": round(directional_consistency_score, 6),
        },
        "penalties": {
            "ambiguity_penalty": round(ambiguity_penalty, 6),
            "conflict_penalty": round(conflict_penalty, 6),
            "freshness_decay_penalty": round(freshness_decay_penalty, 6),
        },
        "weights": {
            "evidence_weight": EVIDENCE_WEIGHT,
            "persistence_weight": PERSISTENCE_WEIGHT,
            "recurrence_weight": RECURRENCE_WEIGHT,
            "directional_weight": DIRECTIONAL_WEIGHT,
            "ambiguity_weight": AMBIGUITY_WEIGHT,
            "conflict_weight": CONFLICT_WEIGHT,
            "freshness_weight": FRESHNESS_WEIGHT,
        },
        "rationale": [
            "Evidence strength blends evidence_count and evidence_confidence.",
            "Higher ambiguity/conflict/lack of freshness reduce edge quality.",
            "Suppression is advisory-only for propagation when score < 0.30.",
        ],
    }

    enriched.update(
        {
            "edge_quality_score": edge_quality_score,
            "evidence_strength_score": evidence_strength_score,
            "persistence_score": persistence_score,
            "recurrence_score": recurrence_score,
            "directional_consistency_score": directional_consistency_score,
            "ambiguity_penalty": ambiguity_penalty,
            "conflict_penalty": conflict_penalty,
            "freshness_decay_penalty": freshness_decay_penalty,
            "decay_adjusted_weight": decay_adjusted_weight,
            "confidence_band": confidence_band,
            "suppressed_for_propagation": suppressed_for_propagation,
            "scoring_version": SCORING_VERSION,
            "explainability_payload": explainability_payload,
        }
    )
    return enriched


def score_edges(edges: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [score_edge_quality(edge) for edge in edges]


def _sample_edges() -> List[Dict[str, Any]]:
    return [
        {
            "source_node_id": "a",
            "target_node_id": "b",
            "edge_type": "mentions",
            "base_weight": 0.8,
            "evidence_count": 8,
            "evidence_confidence": 0.9,
            "recurrence_count": 7,
            "persistence_days": 180,
            "directional_consistency": 0.95,
            "ambiguity_count": 0,
            "conflict_count": 0,
            "last_seen_days_ago": 1,
            "source_table": "sample",
        },
        {
            "source_node_id": "x",
            "target_node_id": "y",
            "edge_type": "weak_link",
            "base_weight": 0.2,
            "evidence_count": 1,
            "evidence_confidence": 0.2,
            "recurrence_count": 0,
            "persistence_days": 2,
            "directional_consistency": 0.1,
            "ambiguity_count": 3,
            "conflict_count": 2,
            "last_seen_days_ago": 30,
            "source_table": "sample",
        },
    ]


def build_summary(scored_edges: List[Dict[str, Any]]) -> Dict[str, Any]:
    high_count = sum(1 for edge in scored_edges if edge["confidence_band"] == "high")
    medium_count = sum(1 for edge in scored_edges if edge["confidence_band"] == "medium")
    low_count = sum(1 for edge in scored_edges if edge["confidence_band"] == "low")
    suppressed_count = sum(
        1 for edge in scored_edges if edge.get("suppressed_for_propagation", False)
    )
    average_score = (
        sum(edge.get("edge_quality_score", 0.0) for edge in scored_edges) / len(scored_edges)
        if scored_edges
        else 0.0
    )
    top_edges = sorted(
        scored_edges,
        key=lambda edge: edge.get("edge_quality_score", 0.0),
        reverse=True,
    )[:5]

    return {
        "tier": "3I",
        "phase": "1A",
        "scoring_version": SCORING_VERSION,
        "edges_scored": len(scored_edges),
        "high_confidence_edges": high_count,
        "medium_confidence_edges": medium_count,
        "low_confidence_edges": low_count,
        "suppressed_edges": suppressed_count,
        "average_edge_quality_score": round(average_score, 6),
        "top_edges": top_edges,
        "status": "success",
    }


def main() -> None:
    scored_edges = score_edges(_sample_edges())
    summary = build_summary(scored_edges)

    output_path = Path("logs/tier3i_edge_quality_summary.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(
        "[tier3i] "
        f"edges_scored={summary['edges_scored']} "
        f"high_confidence_edges={summary['high_confidence_edges']} "
        f"low_confidence_edges={summary['low_confidence_edges']} "
        f"status={summary['status']}"
    )


if __name__ == "__main__":
    main()
