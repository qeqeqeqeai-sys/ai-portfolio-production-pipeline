"""Tier 3I Phase 2B deterministic propagation path explainability."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

SCORING_VERSION = "3I.2B.v1"
MEANINGFUL_REINFORCEMENT_THRESHOLD = 0.05
WEAK_EDGE_QUALITY_THRESHOLD = 0.45


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_band(value: Any) -> str:
    band = str(value or "").lower()
    return band if band in {"high", "medium", "low"} else "low"


def _path_sort_key(path: Dict[str, Any]) -> Tuple[str, str, Tuple[str, ...]]:
    return (
        str(path.get("source_node_id", "")),
        str(path.get("terminal_node_id", "")),
        tuple(str(n) for n in path.get("path_nodes", [])),
    )


def _build_chain(path_nodes: Sequence[Any]) -> str:
    nodes = [str(node) for node in path_nodes if str(node)]
    if not nodes:
        return "unknown_path"
    return " -> ".join(nodes)


def _extract_weak_links(path_edges: Sequence[Dict[str, Any]]) -> List[str]:
    weak_links: List[str] = []
    for edge in path_edges:
        source = str(edge.get("source_node_id", "unknown"))
        target = str(edge.get("target_node_id", "unknown"))
        quality = _to_float(edge.get("edge_quality_score"), 0.0)
        band = _safe_band(edge.get("confidence_band"))

        if band == "low" or quality < WEAK_EDGE_QUALITY_THRESHOLD:
            weak_links.append(f"{source}->{target} (confidence={band}, edge_quality={quality:.3f})")

    return sorted(set(weak_links))


def _confidence_sentence(confidence_band: str) -> str:
    if confidence_band == "high":
        return "Confidence is high based on deterministic path quality scoring and bounded penalties."
    if confidence_band == "medium":
        return "Confidence is medium; the path appears plausible but should be monitored with corroborating evidence."
    return "Confidence is low; this path appears to propagate through weak or ambiguous transmission links."


def _decision_label(path: Dict[str, Any], confidence_band: str) -> str:
    if bool(path.get("contamination_warning", False)):
        return "contaminated_chain"
    if bool(path.get("suppressed_for_propagation", False)):
        return "suppressed_noise"
    if confidence_band in {"high", "medium"}:
        return "actionable_watchlist"
    return "weak_signal"


def explain_paths(multi_hop_paths: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert deterministic path records into readable advisory explanations."""
    paths = sorted((dict(path) for path in multi_hop_paths), key=_path_sort_key)
    explained: List[Dict[str, Any]] = []

    for path in paths:
        path_nodes = list(path.get("path_nodes", []))
        path_edges = [dict(edge) for edge in path.get("path_edges", [])]
        path_id = str(path.get("path_id", "unknown_path"))
        hop_count = int(_to_float(path.get("hop_count"), max(len(path_nodes) - 1, 1)))
        confidence_band = _safe_band(path.get("path_confidence_band"))
        reinforcement_score = _to_float(path.get("reinforcement_score"), 0.0)
        hop_decay = _to_float(path.get("hop_decay_factor"), 1.0)

        chain = _build_chain(path_nodes)
        summary = (
            f"Path {path_id} appears to propagate through {chain} over {hop_count} hop(s) "
            f"with {confidence_band} confidence."
        )

        rationale_parts = [
            "Signal is structurally linked through the ordered node chain.",
            f"Confidence band is {confidence_band} under deterministic scoring.",
        ]

        key_reinforcement_drivers: List[str] = []
        if reinforcement_score >= MEANINGFUL_REINFORCEMENT_THRESHOLD:
            key_reinforcement_drivers.append(
                f"Path reinforcement is meaningful (reinforcement_score={reinforcement_score:.3f})."
            )

        if hop_count > 1:
            rationale_parts.append(
                f"Multi-hop decay was applied (hop_decay_factor={hop_decay:.3f}) to reduce long-chain overstatement."
            )

        weak_links = _extract_weak_links(path_edges)
        if weak_links:
            rationale_parts.append("Weak links were detected in at least one hop.")

        contamination_notes: List[str] = []
        if bool(path.get("contamination_warning", False)):
            contamination_notes.append(
                "Contamination warning present: ambiguity/conflict/suppression signals may distort transmission interpretation."
            )

        warnings = sorted(set(list(path.get("explainability_payload", {}).get("warnings", []))))
        if not path_nodes:
            warnings.append("missing_path_nodes")
        if not path_edges:
            warnings.append("missing_path_edges")

        explained.append(
            {
                "path_id": path_id,
                "causal_chain_summary": summary,
                "path_rationale": " ".join(rationale_parts),
                "key_reinforcement_drivers": key_reinforcement_drivers,
                "weak_links_in_path": weak_links,
                "contamination_notes": contamination_notes,
                "decision_usefulness_label": _decision_label(path, confidence_band),
                "confidence_sentence": _confidence_sentence(confidence_band),
                "explainability_warnings": warnings,
                "scoring_version": SCORING_VERSION,
            }
        )

    return explained


def build_summary(explanations: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    counts = {
        "actionable_watchlist": 0,
        "weak_signal": 0,
        "suppressed_noise": 0,
        "contaminated_chain": 0,
    }
    for record in explanations:
        label = str(record.get("decision_usefulness_label", ""))
        if label in counts:
            counts[label] += 1

    top_explanations = list(explanations[:5])

    return {
        "tier": "3I",
        "phase": "2B",
        "scoring_version": SCORING_VERSION,
        "paths_explained": len(explanations),
        "actionable_watchlist": counts["actionable_watchlist"],
        "weak_signal": counts["weak_signal"],
        "suppressed_noise": counts["suppressed_noise"],
        "contaminated_chain": counts["contaminated_chain"],
        "top_explanations": top_explanations,
        "status": "success",
    }


def _sample_paths() -> List[Dict[str, Any]]:
    return [
        {
            "path_id": "path::a->b->c",
            "source_node_id": "a",
            "terminal_node_id": "c",
            "path_nodes": ["a", "b", "c"],
            "path_edges": [
                {"source_node_id": "a", "target_node_id": "b", "edge_quality_score": 0.81, "confidence_band": "high"},
                {"source_node_id": "b", "target_node_id": "c", "edge_quality_score": 0.68, "confidence_band": "medium"},
            ],
            "hop_count": 2,
            "path_quality_score": 0.62,
            "hop_decay_factor": 0.75,
            "reinforcement_score": 0.08,
            "path_confidence_band": "medium",
            "suppressed_for_propagation": False,
            "contamination_warning": False,
            "explainability_payload": {"warnings": []},
        }
    ]


def main() -> None:
    explanations = explain_paths(_sample_paths())
    summary = build_summary(explanations)

    output_path = Path("logs/tier3i_path_explainability_summary.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(
        "[tier3i] "
        f"paths_explained={summary['paths_explained']} "
        f"actionable_watchlist={summary['actionable_watchlist']} "
        f"suppressed_noise={summary['suppressed_noise']} "
        f"status={summary['status']}"
    )


if __name__ == "__main__":
    main()
