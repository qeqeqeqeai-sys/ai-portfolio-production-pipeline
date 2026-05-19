"""Tier 3I Phase 3A deterministic structural regime intelligence."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

SCORING_VERSION = "3I.3A.v1"


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_len(value: Any) -> int:
    return len(value) if isinstance(value, Sequence) else 0


def _band(value: float, high: float = 0.70, medium: float = 0.45) -> str:
    if value >= high:
        return "high"
    if value >= medium:
        return "medium"
    return "low"


def compute_graph_concentration(structural_influence_nodes: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    nodes = sorted((dict(node) for node in structural_influence_nodes), key=lambda n: str(n.get("node_id", "")))
    scores = [_clip01(_to_float(node.get("structural_influence_score"), 0.0)) for node in nodes]
    total = sum(scores)
    if not scores or total <= 0.0:
        return {
            "graph_concentration_score": 0.0,
            "top_node_dominance_ratio": 0.0,
            "influence_entropy": 1.0,
            "structural_concentration_band": "low",
        }

    normalized = [score / total for score in scores]
    top_ratio = max(normalized)

    n = len(normalized)
    entropy_raw = -sum(p * math.log(p) for p in normalized if p > 0.0)
    entropy_norm = entropy_raw / math.log(n) if n > 1 else 0.0
    influence_entropy = _clip01(entropy_norm)

    inverse_entropy = 1.0 - influence_entropy
    concentration = _clip01((0.55 * top_ratio) + (0.45 * inverse_entropy))
    return {
        "graph_concentration_score": round(concentration, 6),
        "top_node_dominance_ratio": round(_clip01(top_ratio), 6),
        "influence_entropy": round(influence_entropy, 6),
        "structural_concentration_band": _band(concentration),
    }


def compute_fragmentation(quality_scored_edges: Iterable[Dict[str, Any]], multi_hop_paths: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    edges = [dict(edge) for edge in quality_scored_edges]
    paths = [dict(path) for path in multi_hop_paths]
    node_ids: set[str] = set()
    adjacency: Dict[str, set[str]] = {}

    weak_edges = 0
    for edge in edges:
        s = str(edge.get("source_node_id", ""))
        t = str(edge.get("target_node_id", ""))
        if s:
            node_ids.add(s)
        if t:
            node_ids.add(t)
        if s and t:
            adjacency.setdefault(s, set()).add(t)
            adjacency.setdefault(t, set()).add(s)

        quality = _to_float(edge.get("edge_quality_score"), _to_float(edge.get("decay_adjusted_weight"), 0.0))
        if quality < 0.45 or bool(edge.get("suppressed_for_propagation", False)) or str(edge.get("confidence_band", "")).lower() == "low":
            weak_edges += 1

    weak_link_ratio = _clip01((weak_edges / len(edges)) if edges else 0.0)

    # simple deterministic connected-group approximation
    unvisited = set(node_ids)
    components = 0
    while unvisited:
        components += 1
        root = min(unvisited)
        stack = [root]
        unvisited.remove(root)
        while stack:
            cur = stack.pop()
            for nxt in sorted(adjacency.get(cur, set())):
                if nxt in unvisited:
                    unvisited.remove(nxt)
                    stack.append(nxt)

    isolated_cluster_count = max(0, components - 1)
    nodes_count = len(node_ids)
    cluster_factor = _clip01((isolated_cluster_count / max(nodes_count, 1)) * 2.0)

    suppressed_paths = sum(1 for p in paths if bool(p.get("suppressed_for_propagation", False)))
    suppressed_path_ratio = _clip01((suppressed_paths / len(paths)) if paths else 0.0)

    fragmentation = _clip01((0.45 * cluster_factor) + (0.35 * weak_link_ratio) + (0.20 * suppressed_path_ratio))
    connectivity_health_band = "healthy" if fragmentation < 0.30 else "watch" if fragmentation < 0.60 else "fragile"

    return {
        "fragmentation_score": round(fragmentation, 6),
        "isolated_cluster_count": isolated_cluster_count,
        "weak_link_ratio": round(weak_link_ratio, 6),
        "connectivity_health_band": connectivity_health_band,
    }


def compute_propagation_density(quality_scored_edges: Iterable[Dict[str, Any]], multi_hop_paths: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    edges = [dict(edge) for edge in quality_scored_edges]
    paths = [dict(path) for path in multi_hop_paths]
    node_ids = set()
    for edge in edges:
        node_ids.add(str(edge.get("source_node_id", "")))
        node_ids.add(str(edge.get("target_node_id", "")))
    node_ids.discard("")

    high_quality_paths = [
        p for p in paths if _to_float(p.get("path_quality_score"), 0.0) >= 0.70 and not bool(p.get("suppressed_for_propagation", False))
    ]
    base = max(1, len(node_ids))
    density = _clip01(len(high_quality_paths) / base)
    return {
        "propagation_density_score": round(density, 6),
        "high_quality_path_density": round(density, 6),
    }


def compute_overheating(
    transmission_intelligence_summary: Dict[str, Any],
    graph_concentration_score: float,
    high_quality_path_density: float,
    multi_hop_paths: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    summary = dict(transmission_intelligence_summary or {})
    paths = [dict(path) for path in multi_hop_paths]

    reinf = _clip01(_to_float(summary.get("average_reinforcement_score"), 0.0))
    if reinf == 0.0 and paths:
        reinf = _clip01(sum(_to_float(p.get("reinforcement_score"), 0.0) for p in paths) / len(paths))

    contaminated = sum(1 for p in paths if bool(p.get("contamination_warning", False)))
    contagion_pressure = _clip01((contaminated / len(paths)) if paths else 0.0)

    overheating = _clip01(
        (0.35 * reinf) + (0.25 * _clip01(graph_concentration_score)) + (0.25 * _clip01(high_quality_path_density)) + (0.15 * contagion_pressure)
    )
    return {
        "overheating_score": round(overheating, 6),
        "reinforcement_acceleration": round(reinf, 6),
        "contagion_pressure": round(contagion_pressure, 6),
    }


def compute_structural_fragility(
    quality_scored_edges: Iterable[Dict[str, Any]],
    multi_hop_paths: Iterable[Dict[str, Any]],
    graph_concentration_score: float,
    weak_link_ratio: float,
    fragmentation_score: float,
) -> Dict[str, Any]:
    edges = [dict(edge) for edge in quality_scored_edges]
    paths = [dict(path) for path in multi_hop_paths]

    suppressed_ratio = _clip01((sum(1 for edge in edges if bool(edge.get("suppressed_for_propagation", False))) / len(edges)) if edges else 0.0)
    contamination_ratio = _clip01((sum(1 for p in paths if bool(p.get("contamination_warning", False))) / len(paths)) if paths else 0.0)

    concentration_connectivity_penalty = _clip01(_clip01(graph_concentration_score) * _clip01(fragmentation_score))
    fragility = _clip01(
        (0.30 * suppressed_ratio)
        + (0.25 * contamination_ratio)
        + (0.20 * _clip01(weak_link_ratio))
        + (0.25 * concentration_connectivity_penalty)
    )
    return {
        "structural_fragility_score": round(fragility, 6),
        "suppression_ratio": round(suppressed_ratio, 6),
        "contamination_ratio": round(contamination_ratio, 6),
    }


def compute_structural_stability(
    propagation_density_score: float,
    contamination_ratio: float,
    fragmentation_score: float,
    graph_concentration_score: float,
) -> Dict[str, Any]:
    moderate_concentration = 1.0 - abs(_clip01(graph_concentration_score) - 0.50) / 0.50
    stability = _clip01(
        (0.35 * _clip01(propagation_density_score))
        + (0.25 * (1.0 - _clip01(contamination_ratio)))
        + (0.25 * (1.0 - _clip01(fragmentation_score)))
        + (0.15 * _clip01(moderate_concentration))
    )
    return {"structural_stability_score": round(stability, 6)}


def classify_regime_state(metrics: Dict[str, Any]) -> Tuple[str, bool]:
    overheating = _to_float(metrics.get("overheating_score"), 0.0)
    fragmentation = _to_float(metrics.get("fragmentation_score"), 0.0)
    fragility = _to_float(metrics.get("structural_fragility_score"), 0.0)
    stability = _to_float(metrics.get("structural_stability_score"), 0.0)
    density = _to_float(metrics.get("propagation_density_score"), 0.0)

    if overheating >= 0.70:
        state = "overheated"
    elif fragmentation >= 0.65:
        state = "fragmented"
    elif fragility >= 0.62:
        state = "fragile"
    elif density >= 0.60 and stability >= 0.55 and fragility < 0.45:
        state = "expanding"
    elif stability >= 0.62 and fragility < 0.40 and fragmentation < 0.40 and overheating < 0.55:
        state = "stable"
    else:
        state = "transitioning"

    warning = state == "transitioning" or (abs(overheating - 0.70) < 0.05) or (abs(fragmentation - 0.65) < 0.05)
    return state, warning


def build_explainability_payload(metrics: Dict[str, Any]) -> Dict[str, Any]:
    state = str(metrics.get("regime_state", "transitioning"))
    rationale = [
        f"Regime classified as {state} using deterministic bounded threshold logic.",
        f"Concentration={_to_float(metrics.get('graph_concentration_score')):.3f}, fragmentation={_to_float(metrics.get('fragmentation_score')):.3f}, overheating={_to_float(metrics.get('overheating_score')):.3f}.",
    ]
    warnings = []
    if metrics.get("regime_transition_warning"):
        warnings.append("Regime sits near one or more transition boundaries.")
    if _to_float(metrics.get("contagion_pressure"), 0.0) > 0.4:
        warnings.append("Contagion pressure is elevated.")

    drivers = sorted(
        [
            ("graph_concentration_score", _to_float(metrics.get("graph_concentration_score"), 0.0)),
            ("fragmentation_score", _to_float(metrics.get("fragmentation_score"), 0.0)),
            ("overheating_score", _to_float(metrics.get("overheating_score"), 0.0)),
            ("structural_fragility_score", _to_float(metrics.get("structural_fragility_score"), 0.0)),
            ("propagation_density_score", _to_float(metrics.get("propagation_density_score"), 0.0)),
        ],
        key=lambda item: (-item[1], item[0]),
    )

    return {
        "regime_rationale": rationale,
        "key_contributing_metrics": {
            "graph_concentration_score": _to_float(metrics.get("graph_concentration_score"), 0.0),
            "fragmentation_score": _to_float(metrics.get("fragmentation_score"), 0.0),
            "overheating_score": _to_float(metrics.get("overheating_score"), 0.0),
            "structural_fragility_score": _to_float(metrics.get("structural_fragility_score"), 0.0),
            "structural_stability_score": _to_float(metrics.get("structural_stability_score"), 0.0),
        },
        "warnings": warnings,
        "dominant_structural_drivers": [name for name, _ in drivers[:3]],
        "concentration_explanation": "Concentration blends top-node dominance with inverse influence entropy.",
        "fragility_explanation": "Fragility rises with suppression, contamination, weak links, and concentrated weak connectivity.",
        "overheating_explanation": "Overheating rises with reinforcement acceleration, concentration, high-quality path density, and contagion pressure.",
        "connectivity_explanation": "Connectivity health is inferred from weak links, suppressed paths, and isolated cluster approximation.",
    }


def compute_structural_regime(
    quality_scored_edges: Iterable[Dict[str, Any]],
    structural_influence_nodes: Iterable[Dict[str, Any]],
    multi_hop_paths: Iterable[Dict[str, Any]] | None = None,
    path_explanations: Iterable[Dict[str, Any]] | None = None,
    transmission_intelligence_summary: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    paths = [dict(path) for path in (multi_hop_paths or [])]
    _ = [dict(record) for record in (path_explanations or [])]

    concentration = compute_graph_concentration(structural_influence_nodes)
    fragmentation = compute_fragmentation(quality_scored_edges, paths)
    propagation = compute_propagation_density(quality_scored_edges, paths)
    overheating = compute_overheating(
        transmission_intelligence_summary or {},
        concentration["graph_concentration_score"],
        propagation["high_quality_path_density"],
        paths,
    )
    fragility = compute_structural_fragility(
        quality_scored_edges,
        paths,
        concentration["graph_concentration_score"],
        fragmentation["weak_link_ratio"],
        fragmentation["fragmentation_score"],
    )
    stability = compute_structural_stability(
        propagation["propagation_density_score"],
        fragility["contamination_ratio"],
        fragmentation["fragmentation_score"],
        concentration["graph_concentration_score"],
    )

    metrics: Dict[str, Any] = {
        "tier": "3I",
        "phase": "3A",
        "scoring_version": SCORING_VERSION,
        **concentration,
        **fragmentation,
        **overheating,
        **propagation,
        **fragility,
        **stability,
    }
    state, warning = classify_regime_state(metrics)
    metrics["regime_state"] = state
    metrics["regime_transition_warning"] = warning
    metrics["explainability_payload"] = build_explainability_payload(metrics)
    metrics["top_structural_drivers"] = metrics["explainability_payload"]["dominant_structural_drivers"]
    metrics["status"] = "success"
    return metrics


def _sample_inputs() -> Dict[str, Any]:
    return {
        "quality_scored_edges": [
            {"source_node_id": "a", "target_node_id": "b", "edge_quality_score": 0.85, "confidence_band": "high"},
            {"source_node_id": "b", "target_node_id": "c", "edge_quality_score": 0.78, "confidence_band": "high"},
            {"source_node_id": "a", "target_node_id": "d", "edge_quality_score": 0.42, "confidence_band": "medium", "suppressed_for_propagation": True},
        ],
        "structural_influence_nodes": [
            {"node_id": "a", "structural_influence_score": 0.9},
            {"node_id": "b", "structural_influence_score": 0.6},
            {"node_id": "c", "structural_influence_score": 0.4},
            {"node_id": "d", "structural_influence_score": 0.2},
        ],
        "multi_hop_paths": [
            {"path_id": "p1", "path_quality_score": 0.82, "reinforcement_score": 0.2, "contamination_warning": False},
            {"path_id": "p2", "path_quality_score": 0.35, "reinforcement_score": 0.05, "suppressed_for_propagation": True, "contamination_warning": True},
        ],
        "path_explanations": [{"path_id": "p1", "decision_usefulness_label": "actionable_watchlist"}],
        "transmission_intelligence_summary": {"average_reinforcement_score": 0.125},
    }


def main() -> None:
    sample = _sample_inputs()
    result = compute_structural_regime(**sample)
    summary = {
        "tier": "3I",
        "phase": "3A",
        "scoring_version": SCORING_VERSION,
        "regime_state": result["regime_state"],
        "graph_concentration_score": result["graph_concentration_score"],
        "fragmentation_score": result["fragmentation_score"],
        "overheating_score": result["overheating_score"],
        "propagation_density_score": result["propagation_density_score"],
        "structural_fragility_score": result["structural_fragility_score"],
        "structural_stability_score": result["structural_stability_score"],
        "regime_transition_warning": result["regime_transition_warning"],
        "top_structural_drivers": result["top_structural_drivers"],
        "status": "success",
    }

    output_path = Path("logs/tier3i_structural_regime_summary.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(
        "[tier3i] "
        f"regime_state={summary['regime_state']} "
        f"concentration={summary['graph_concentration_score']:.3f} "
        f"fragility={summary['structural_fragility_score']:.3f} "
        f"overheating={summary['overheating_score']:.3f} "
        f"status={summary['status']}"
    )


if __name__ == "__main__":
    main()
