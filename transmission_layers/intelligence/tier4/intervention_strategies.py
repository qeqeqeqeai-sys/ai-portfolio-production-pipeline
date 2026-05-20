from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

from .scenario_semantics import clamp_score


def _sorted_nodes(nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(nodes, key=lambda n: str(n.get("node_id", "")))


def _sorted_edges(edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(edges, key=lambda e: (str(e.get("source_node_id", "")), str(e.get("target_node_id", ""))))


def reinforce_nodes(state: Dict[str, Any], target_nodes: List[str], strength: float = 0.2) -> Dict[str, Any]:
    out = deepcopy(state)
    targets = set(sorted(str(n) for n in target_nodes))
    for node in _sorted_nodes(out.get("structural_influence_nodes", [])):
        if str(node.get("node_id", "")) in targets:
            node["resilience_score"] = clamp_score(node.get("resilience_score", 0.0) + strength)
            node["traffic_score"] = clamp_score(node.get("traffic_score", 0.0) * (1.0 - clamp_score(strength, 0.0, 0.8) * 0.5))
    return out


def isolate_corridors(state: Dict[str, Any], target_corridors: List[str]) -> Dict[str, Any]:
    out = deepcopy(state)
    targets = set(sorted(str(c) for c in target_corridors))
    retained = []
    for edge in _sorted_edges(out.get("quality_scored_edges", [])):
        cid = f"{edge.get('source_node_id','')}->{edge.get('target_node_id','')}"
        if cid not in targets:
            retained.append(edge)
    out["quality_scored_edges"] = retained
    return out


def suppress_cascade_paths(state: Dict[str, Any], target_corridors: List[str]) -> Dict[str, Any]:
    out = deepcopy(state)
    targets = set(sorted(str(c) for c in target_corridors))
    for edge in _sorted_edges(out.get("quality_scored_edges", [])):
        cid = f"{edge.get('source_node_id','')}->{edge.get('target_node_id','')}"
        if not targets or cid in targets:
            edge["suppressed_for_propagation"] = True
    return out


def reinforce_resilience(state: Dict[str, Any], target_nodes: List[str], strength: float = 0.15) -> Dict[str, Any]:
    return reinforce_nodes(state, target_nodes, strength)


def reduce_overload(state: Dict[str, Any], target_nodes: List[str], strength: float = 0.2) -> Dict[str, Any]:
    out = deepcopy(state)
    targets = set(sorted(str(n) for n in target_nodes))
    for node in _sorted_nodes(out.get("structural_influence_nodes", [])):
        if str(node.get("node_id", "")) in targets:
            node["traffic_score"] = clamp_score(node.get("traffic_score", 0.0) * (1.0 - clamp_score(strength, 0.0, 0.9)))
            node["contagion_score"] = clamp_score(node.get("contagion_score", 0.0) * (1.0 - clamp_score(strength, 0.0, 0.9) * 0.5))
    return out


def contain_fragmentation(state: Dict[str, Any], target_corridors: List[str]) -> Dict[str, Any]:
    out = suppress_cascade_paths(state, target_corridors)
    for edge in _sorted_edges(out.get("quality_scored_edges", [])):
        if edge.get("suppressed_for_propagation"):
            edge["edge_quality_score"] = clamp_score(edge.get("edge_quality_score", 0.0) + 0.1)
    return out
