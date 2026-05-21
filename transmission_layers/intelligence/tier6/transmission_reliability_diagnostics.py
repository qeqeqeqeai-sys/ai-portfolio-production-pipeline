"""Tier 6B deterministic transmission reliability decomposition diagnostics."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, List

from transmission_layers.operationalization.serialization import stable_checksum

STATUS_VALUES = {"ok", "review", "insufficient_structure"}
CAUSAL_DIAGNOSTIC_LABELS = {
    "causal_path_traceable",
    "causal_path_partially_traceable",
    "causal_path_weak_traceability",
}
EDGE_DIAGNOSTIC_LABELS = {"edge_reliable", "edge_moderate", "edge_weak"}
NODE_DIAGNOSTIC_LABELS = {"node_stable", "node_moderate", "node_unstable"}
FAILURE_MODES = {
    "none",
    "disconnected_topology",
    "weak_edge_reliability",
    "unstable_node_influence",
    "noisy_propagation",
    "weak_causal_traceability",
}


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _bounded_score(value: float) -> float:
    return max(0.0, min(1.0, round(_to_float(value), 6)))


def _sorted_nodes(topology: Dict[str, Any]) -> List[Dict[str, Any]]:
    nodes = topology.get("nodes", [])
    if not isinstance(nodes, list):
        return []
    return sorted((dict(n) for n in nodes if isinstance(n, dict)), key=lambda n: str(n.get("node_id", "")))


def _sorted_edges(topology: Dict[str, Any]) -> List[Dict[str, Any]]:
    edges = topology.get("edges", [])
    if not isinstance(edges, list):
        return []
    return sorted(
        (dict(e) for e in edges if isinstance(e, dict)),
        key=lambda e: (str(e.get("source_node_id", "")), str(e.get("target_node_id", ""))),
    )


def _structural_connectivity(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> float:
    if not nodes:
        return 0.0
    max_edges = len(nodes) * max(len(nodes) - 1, 1)
    return _bounded_score(len(edges) / max_edges)


def _edge_consistency(edges: Iterable[Dict[str, Any]]) -> tuple[float, List[Dict[str, Any]]]:
    scores: List[float] = []
    diag: List[Dict[str, Any]] = []
    for edge in edges:
        eq = _bounded_score(_to_float(edge.get("edge_quality_score"), 0.0))
        suppressed = bool(edge.get("suppressed_for_propagation", False))
        consistency = _bounded_score(eq * (0.7 if suppressed else 1.0))
        if consistency >= 0.70:
            label = "edge_reliable"
        elif consistency >= 0.45:
            label = "edge_moderate"
        else:
            label = "edge_weak"
        scores.append(consistency)
        diag.append({
            "source_node_id": str(edge.get("source_node_id", "")),
            "target_node_id": str(edge.get("target_node_id", "")),
            "edge_consistency_score": consistency,
            "edge_diagnostic_label": label,
        })
    return _bounded_score(sum(scores) / len(scores) if scores else 0.0), diag


def _node_stability(nodes: Iterable[Dict[str, Any]]) -> tuple[float, List[Dict[str, Any]]]:
    scores: List[float] = []
    diag: List[Dict[str, Any]] = []
    for node in nodes:
        influence = _bounded_score(_to_float(node.get("influence_score"), 0.0))
        resilience = _bounded_score(_to_float(node.get("resilience_score"), 0.0))
        contagion = _bounded_score(_to_float(node.get("contagion_score"), 0.0))
        stability = _bounded_score(0.45 * influence + 0.35 * resilience + 0.20 * (1.0 - contagion))
        if stability >= 0.70:
            label = "node_stable"
        elif stability >= 0.45:
            label = "node_moderate"
        else:
            label = "node_unstable"
        scores.append(stability)
        diag.append({"node_id": str(node.get("node_id", "")), "node_stability_score": stability, "node_diagnostic_label": label})
    return _bounded_score(sum(scores) / len(scores) if scores else 0.0), diag


def _propagation_cleanliness(edges: Iterable[Dict[str, Any]]) -> float:
    vals: List[float] = []
    for edge in edges:
        eq = _bounded_score(_to_float(edge.get("edge_quality_score"), 0.0))
        suppressed = 1.0 if bool(edge.get("suppressed_for_propagation", False)) else 0.0
        vals.append(_bounded_score(1.0 - (0.60 * (1.0 - eq) + 0.40 * suppressed)))
    return _bounded_score(sum(vals) / len(vals) if vals else 0.0)


def _causal_traceability(edges: List[Dict[str, Any]], nodes: List[Dict[str, Any]]) -> float:
    if not nodes:
        return 0.0
    if not edges:
        return 0.0
    represented = {(str(e.get("source_node_id", "")), str(e.get("target_node_id", ""))) for e in edges}
    unique_node_refs = {src for src, _ in represented} | {dst for _, dst in represented}
    coverage = _bounded_score(len(unique_node_refs) / len(nodes))
    return coverage


def assess_transmission_reliability_diagnostics(topology: Dict[str, Any]) -> Dict[str, Any]:
    topology_view = deepcopy(topology) if isinstance(topology, dict) else {}
    nodes = _sorted_nodes(topology_view)
    edges = _sorted_edges(topology_view)

    structural_connectivity_score = _structural_connectivity(nodes, edges)
    edge_consistency_score, edge_diagnostics = _edge_consistency(edges)
    node_stability_score, node_diagnostics = _node_stability(nodes)
    propagation_cleanliness_score = _propagation_cleanliness(edges)
    causal_traceability_score = _causal_traceability(edges, nodes)

    if not nodes or not edges:
        causal_label = "causal_path_weak_traceability"
    elif causal_traceability_score >= 0.80:
        causal_label = "causal_path_traceable"
    elif causal_traceability_score >= 0.50:
        causal_label = "causal_path_partially_traceable"
    else:
        causal_label = "causal_path_weak_traceability"

    transmission_reliability_score = _bounded_score(
        0.20 * structural_connectivity_score
        + 0.25 * edge_consistency_score
        + 0.20 * node_stability_score
        + 0.20 * propagation_cleanliness_score
        + 0.15 * causal_traceability_score
    )

    failure_modes: List[str] = []
    if nodes and not edges:
        failure_modes.append("disconnected_topology")
    if any(d["edge_diagnostic_label"] == "edge_weak" for d in edge_diagnostics):
        failure_modes.append("weak_edge_reliability")
    if any(d["node_diagnostic_label"] == "node_unstable" for d in node_diagnostics):
        failure_modes.append("unstable_node_influence")
    if propagation_cleanliness_score < 0.45:
        failure_modes.append("noisy_propagation")
    if causal_label == "causal_path_weak_traceability":
        failure_modes.append("weak_causal_traceability")
    if not failure_modes:
        failure_modes.append("none")

    if not nodes or not edges:
        status = "insufficient_structure"
    elif transmission_reliability_score >= 0.65 and failure_modes == ["none"]:
        status = "ok"
    else:
        status = "review"

    result = {
        "status": status,
        "transmission_reliability_score": transmission_reliability_score,
        "reliability_components": {
            "structural_connectivity_score": structural_connectivity_score,
            "edge_consistency_score": edge_consistency_score,
            "node_stability_score": node_stability_score,
            "propagation_cleanliness_score": propagation_cleanliness_score,
            "causal_traceability_score": causal_traceability_score,
        },
        "causal_diagnostic_labels": [causal_label],
        "edge_diagnostics": edge_diagnostics,
        "node_diagnostics": node_diagnostics,
        "transmission_failure_modes": failure_modes,
        "diagnostics": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "empty_topology": len(nodes) == 0 and len(edges) == 0,
            "disconnected_topology": len(nodes) > 0 and len(edges) == 0,
            "bounded_scores_valid": True,
            "controlled_vocabularies_enforced": True,
        },
        "explanation": (
            "Tier 6B deterministic transmission reliability decomposition executed with bounded component scoring, "
            "sorted diagnostics ordering, controlled label vocabularies, and additive-only causal failure-mode tracing."
        ),
    }
    result["checksum"] = stable_checksum(result, prefix="tier6b")
    return result
