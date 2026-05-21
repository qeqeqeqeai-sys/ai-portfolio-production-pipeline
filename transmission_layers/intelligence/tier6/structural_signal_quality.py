"""Tier 6A deterministic structural signal quality intelligence."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, List, Tuple

from transmission_layers.operationalization.serialization import stable_checksum


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
    return sorted((dict(node) for node in nodes if isinstance(node, dict)), key=lambda n: str(n.get("node_id", "")))


def _sorted_edges(topology: Dict[str, Any]) -> List[Dict[str, Any]]:
    edges = topology.get("edges", [])
    if not isinstance(edges, list):
        return []
    return sorted(
        (dict(edge) for edge in edges if isinstance(edge, dict)),
        key=lambda e: (str(e.get("source_node_id", "")), str(e.get("target_node_id", ""))),
    )


def _signal_quality_score(nodes: Iterable[Dict[str, Any]]) -> Tuple[float, List[Dict[str, Any]]]:
    inventory: List[Dict[str, Any]] = []
    scores: List[float] = []
    for node in nodes:
        node_id = str(node.get("node_id", ""))
        influence = _bounded_score(_to_float(node.get("influence_score"), 0.0))
        centrality = _bounded_score(_to_float(node.get("centrality_score"), 0.0))
        resilience = _bounded_score(_to_float(node.get("resilience_score"), 0.0))
        fragmentation = _bounded_score(_to_float(node.get("fragmentation_score"), 0.0))
        quality = _bounded_score(0.35 * influence + 0.30 * centrality + 0.20 * resilience + 0.15 * (1.0 - fragmentation))
        scores.append(quality)
        inventory.append({"node_id": node_id, "signal_quality_score": quality, "stability_inputs": {"influence_score": influence, "centrality_score": centrality, "resilience_score": resilience, "fragmentation_score": fragmentation}})
    return _bounded_score(sum(scores) / len(scores) if scores else 0.0), inventory


def _edge_reliability_score(edges: Iterable[Dict[str, Any]]) -> Tuple[float, List[Dict[str, Any]], int]:
    inventory: List[Dict[str, Any]] = []
    scores: List[float] = []
    weak_count = 0
    for edge in edges:
        src = str(edge.get("source_node_id", ""))
        dst = str(edge.get("target_node_id", ""))
        edge_quality = _bounded_score(_to_float(edge.get("edge_quality_score"), 0.0))
        suppressed = bool(edge.get("suppressed_for_propagation", False))
        suppression_penalty = 0.30 if suppressed else 0.0
        reliability = _bounded_score(edge_quality * (1.0 - suppression_penalty))
        if reliability < 0.45:
            weak_count += 1
        scores.append(reliability)
        inventory.append({"source_node_id": src, "target_node_id": dst, "edge_reliability_score": reliability, "suppressed_for_propagation": suppressed})
    return _bounded_score(sum(scores) / len(scores) if scores else 0.0), inventory, weak_count


def _node_influence_stability_score(nodes: Iterable[Dict[str, Any]]) -> float:
    vals: List[float] = []
    for node in nodes:
        influence = _bounded_score(_to_float(node.get("influence_score"), 0.0))
        contagion = _bounded_score(_to_float(node.get("contagion_score"), 0.0))
        resilience = _bounded_score(_to_float(node.get("resilience_score"), 0.0))
        vals.append(_bounded_score(0.45 * influence + 0.25 * resilience + 0.30 * (1.0 - contagion)))
    return _bounded_score(sum(vals) / len(vals) if vals else 0.0)


def _propagation_noise_score(edges: Iterable[Dict[str, Any]]) -> float:
    penalties: List[float] = []
    for edge in edges:
        eq = _bounded_score(_to_float(edge.get("edge_quality_score"), 0.0))
        suppressed = 1.0 if bool(edge.get("suppressed_for_propagation", False)) else 0.0
        penalties.append(_bounded_score(0.65 * (1.0 - eq) + 0.35 * suppressed))
    return _bounded_score(sum(penalties) / len(penalties) if penalties else 1.0)


def _weak_links(edge_inventory: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    weak = [dict(edge) for edge in edge_inventory if _to_float(edge.get("edge_reliability_score"), 0.0) < 0.45]
    return sorted(weak, key=lambda e: (str(e.get("source_node_id", "")), str(e.get("target_node_id", ""))))


def _confidence_label(signal_quality: float, reliability: float, stability: float, node_count: int, edge_count: int) -> str:
    if node_count == 0 or edge_count == 0:
        return "insufficient_structure"
    composite = _bounded_score(0.35 * signal_quality + 0.35 * reliability + 0.30 * stability)
    if composite >= 0.75:
        return "strong"
    if composite >= 0.50:
        return "moderate"
    return "weak"


def assess_structural_signal_quality(topology: Dict[str, Any]) -> Dict[str, Any]:
    topology_view = deepcopy(topology) if isinstance(topology, dict) else {}
    nodes = _sorted_nodes(topology_view)
    edges = _sorted_edges(topology_view)

    signal_quality, node_inventory = _signal_quality_score(nodes)
    transmission_reliability, edge_inventory, _ = _edge_reliability_score(edges)
    influence_stability = _node_influence_stability_score(nodes)
    propagation_noise = _propagation_noise_score(edges)
    weak_links = _weak_links(edge_inventory)
    label = _confidence_label(signal_quality, transmission_reliability, influence_stability, len(nodes), len(edges))

    diagnostics = {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "disconnected_topology": len(nodes) > 0 and len(edges) == 0,
        "empty_topology": len(nodes) == 0 and len(edges) == 0,
        "bounded_scores_valid": True,
    }

    result = {
        "assessment_status": "success",
        "signal_quality_score": signal_quality,
        "transmission_reliability_score": transmission_reliability,
        "node_influence_stability_score": influence_stability,
        "propagation_noise_score": propagation_noise,
        "weak_link_count": len(weak_links),
        "confidence_label": label,
        "node_quality_inventory": node_inventory,
        "edge_reliability_inventory": edge_inventory,
        "weak_links": weak_links,
        "diagnostics": diagnostics,
        "explanation": (
            "Tier 6A deterministic structural signal quality assessment executed with bounded scoring, "
            "sorted topology inventories, and weak-link diagnostics."
        ),
    }
    result["checksum"] = stable_checksum(result, prefix="tier6a")
    return result
