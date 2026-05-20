from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

from .scenario_semantics import clamp_score, normalize_structural_scenario


def _stable_edges(edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(edges, key=lambda e: (str(e.get("source_node_id", "")), str(e.get("target_node_id", ""))))


def remove_corridors(state: Dict[str, Any], targets: List[str]) -> Dict[str, Any]:
    edges = []
    target_set = set(targets)
    for edge in _stable_edges(state.get("quality_scored_edges", [])):
        cid = f"{edge.get('source_node_id','')}->{edge.get('target_node_id','')}"
        if cid not in target_set:
            edges.append(edge)
    state["quality_scored_edges"] = edges
    return state


def stress_nodes(state: Dict[str, Any], targets: List[str], strength: float) -> Dict[str, Any]:
    target_set = set(targets)
    for node in sorted(state.get("structural_influence_nodes", []), key=lambda n: str(n.get("node_id", ""))):
        if str(node.get("node_id", "")) in target_set:
            node["influence_score"] = clamp_score(node.get("influence_score", 0.0) * (1.0 + 0.5 * strength))
            node["contagion_score"] = clamp_score(node.get("contagion_score", 0.0) * (1.0 + 0.5 * strength))
            node["traffic_score"] = clamp_score(node.get("traffic_score", 0.0) * (1.0 + 0.4 * strength))
    return state


def degrade_corridors(state: Dict[str, Any], targets: List[str], strength: float) -> Dict[str, Any]:
    target_set = set(targets)
    for edge in _stable_edges(state.get("quality_scored_edges", [])):
        cid = f"{edge.get('source_node_id','')}->{edge.get('target_node_id','')}"
        if cid in target_set:
            edge["edge_quality_score"] = clamp_score(edge.get("edge_quality_score", 0.0) * (1.0 - 0.7 * strength))
    return state


def reduce_resilience(state: Dict[str, Any], targets: List[str], strength: float) -> Dict[str, Any]:
    target_set = set(targets)
    for node in sorted(state.get("structural_influence_nodes", []), key=lambda n: str(n.get("node_id", ""))):
        if not target_set or str(node.get("node_id", "")) in target_set:
            node["resilience_score"] = clamp_score(node.get("resilience_score", 0.0) * (1.0 - 0.8 * strength))
    return state


def apply_suppression_probe(state: Dict[str, Any], targets: List[str], strength: float) -> Dict[str, Any]:
    target_set = set(targets)
    for edge in _stable_edges(state.get("quality_scored_edges", [])):
        cid = f"{edge.get('source_node_id','')}->{edge.get('target_node_id','')}"
        if not target_set or cid in target_set:
            edge["suppressed_for_propagation"] = bool(strength > 0.0)
    return state


def apply_structural_perturbation(inputs: Dict[str, Any], scenario: Dict[str, Any]) -> Dict[str, Any]:
    norm = normalize_structural_scenario(scenario)
    out = deepcopy(inputs)
    s_type = norm["scenario_type"]
    strength = clamp_score(norm["perturbation_strength"])
    if s_type == "baseline":
        pass
    elif s_type == "corridor_removed":
        out = remove_corridors(out, norm["target_corridors"])
    elif s_type in {"node_stressed", "chokepoint_stressed", "overload_probe"}:
        out = stress_nodes(out, norm["target_nodes"], strength)
    elif s_type in {"corridor_degraded", "fragmentation_probe"}:
        out = degrade_corridors(out, norm["target_corridors"], strength)
    elif s_type == "suppression_applied":
        out = apply_suppression_probe(out, norm["target_corridors"], strength)
    elif s_type == "resilience_reduced":
        out = reduce_resilience(out, norm["target_nodes"], strength)
    else:
        out.setdefault("scenario_diagnostics", {})["unsupported_scenario_type"] = s_type
    out.setdefault("scenario_diagnostics", {}).update({
        "scenario_id": norm["scenario_id"],
        "scenario_type": s_type,
        "scenario_checksum": norm["scenario_checksum"],
    })
    return out
