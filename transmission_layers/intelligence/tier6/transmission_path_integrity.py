"""Tier 6C deterministic transmission path integrity and bottleneck attribution."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, List, Set, Tuple

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
    def _key(e: Dict[str, Any]) -> Tuple[str, str, str]:
        src = str(e.get("source_node_id", ""))
        dst = str(e.get("target_node_id", ""))
        edge_id = str(e.get("edge_id", f"{src}->{dst}"))
        return (src, dst, edge_id)

    return sorted((dict(edge) for edge in edges if isinstance(edge, dict)), key=_key)


def _build_graph(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> Tuple[List[str], Dict[str, Set[str]], Dict[Tuple[str, str], Dict[str, Any]]]:
    node_ids = [str(node.get("node_id", "")) for node in nodes]
    adjacency: Dict[str, Set[str]] = {node_id: set() for node_id in node_ids}
    edge_map: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for edge in edges:
        src = str(edge.get("source_node_id", ""))
        dst = str(edge.get("target_node_id", ""))
        if src in adjacency and dst in adjacency:
            adjacency[src].add(dst)
            edge_map[(src, dst)] = edge
    return node_ids, adjacency, edge_map


def _reachable_from(start: str, adjacency: Dict[str, Set[str]]) -> Set[str]:
    if start not in adjacency:
        return set()
    seen: Set[str] = {start}
    queue: List[str] = [start]
    while queue:
        node = queue.pop(0)
        for nxt in sorted(adjacency.get(node, set())):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen


def _enumerate_paths(node_ids: List[str], adjacency: Dict[str, Set[str]], edge_map: Dict[Tuple[str, str], Dict[str, Any]]) -> List[Dict[str, Any]]:
    paths: List[Dict[str, Any]] = []
    for src in sorted(node_ids):
        for dst in sorted(node_ids):
            if src == dst:
                continue
            if dst in adjacency.get(src, set()):
                edge = edge_map.get((src, dst), {})
                path_len = 1
                metadata_ok = bool(edge.get("edge_quality_score") is not None and edge.get("suppressed_for_propagation") is not None)
                edge_quality = _bounded_score(_to_float(edge.get("edge_quality_score"), 0.0))
                path_score = _bounded_score(0.60 + 0.40 * edge_quality) if metadata_ok else _bounded_score(0.40 * edge_quality)
                paths.append({
                    "path_id": f"{src}->{dst}",
                    "source": src,
                    "target": dst,
                    "path_length": path_len,
                    "path_integrity_score": path_score,
                    "metadata_ok": metadata_ok,
                })
    return sorted(paths, key=lambda p: (p["source"], p["target"], p["path_id"]))


def assess_transmission_path_integrity(topology: Dict[str, Any]) -> Dict[str, Any]:
    topology_view = deepcopy(topology) if isinstance(topology, dict) else {}
    nodes = _sorted_nodes(topology_view)
    edges = _sorted_edges(topology_view)
    node_ids, adjacency, edge_map = _build_graph(nodes, edges)

    missing_nodes = len(nodes) == 0
    missing_edges = len(edges) == 0
    is_empty = missing_nodes and missing_edges

    paths = _enumerate_paths(node_ids, adjacency, edge_map)
    path_count = len(paths)
    reachable_pairs = path_count
    possible_pairs = max(len(node_ids) * (len(node_ids) - 1), 1)

    path_connectivity_score = _bounded_score(reachable_pairs / possible_pairs if node_ids else 0.0)
    route_redundancy_score = _bounded_score(1.0 if path_count > len(node_ids) else (0.5 if path_count > 0 else 0.0))

    dep_counts = {node_id: 0 for node_id in node_ids}
    for edge in edges:
        src = str(edge.get("source_node_id", ""))
        dst = str(edge.get("target_node_id", ""))
        if src in dep_counts:
            dep_counts[src] += 1
        if dst in dep_counts:
            dep_counts[dst] += 1
    max_dep = max(dep_counts.values()) if dep_counts else 0
    bottleneck_resilience_score = _bounded_score(1.0 - (max_dep / max(len(edges), 1)) if edges else 0.0)

    complete_edge_meta = 0
    for edge in edges:
        if edge.get("edge_quality_score") is not None and edge.get("suppressed_for_propagation") is not None:
            complete_edge_meta += 1
    edge_path_consistency_score = _bounded_score(complete_edge_meta / len(edges) if edges else 0.0)
    trace_continuity_score = _bounded_score(path_connectivity_score)

    component_scores = {
        "path_connectivity_score": path_connectivity_score,
        "route_redundancy_score": route_redundancy_score,
        "bottleneck_resilience_score": bottleneck_resilience_score,
        "edge_path_consistency_score": edge_path_consistency_score,
        "trace_continuity_score": trace_continuity_score,
    }
    path_integrity_score = _bounded_score(sum(component_scores.values()) / len(component_scores))

    path_diagnostics = []
    for p in paths:
        if not p["metadata_ok"]:
            label = "incomplete_path_metadata"
        elif p["path_integrity_score"] < 0.35:
            label = "broken_path"
        elif p["path_integrity_score"] < 0.60:
            label = "weak_path"
        elif max_dep > 0 and any(dep_counts.get(node, 0) >= max_dep and dep_counts.get(node, 0) > 1 for node in (p["source"], p["target"])):
            label = "bottleneck_path"
        else:
            label = "stable_path"
        path_diagnostics.append({
            "path_id": p["path_id"], "source": p["source"], "target": p["target"],
            "path_length": p["path_length"], "path_integrity_score": p["path_integrity_score"], "diagnostic_label": label,
        })

    bottleneck_nodes = []
    for node_id in sorted(node_ids):
        dep = dep_counts.get(node_id, 0)
        score = _bounded_score(dep / max(max_dep, 1)) if max_dep else 0.0
        if dep == 0:
            label = "isolated_node"
        elif score >= 0.8 and dep > 1:
            label = "bottleneck_node"
        elif score >= 0.4:
            label = "moderate_dependency_node"
        else:
            label = "low_dependency_node"
        bottleneck_nodes.append({"node_id": node_id, "bottleneck_score": score, "dependency_count": dep, "diagnostic_label": label})

    bottleneck_edges = []
    for edge in edges:
        src = str(edge.get("source_node_id", ""))
        dst = str(edge.get("target_node_id", ""))
        edge_id = str(edge.get("edge_id", f"{src}->{dst}"))
        complete = edge.get("edge_quality_score") is not None and edge.get("suppressed_for_propagation") is not None
        score = _bounded_score((dep_counts.get(src, 0) + dep_counts.get(dst, 0)) / max(2 * max_dep, 1)) if max_dep else 0.0
        if not complete:
            label = "incomplete_edge"
        elif score >= 0.75:
            label = "bottleneck_edge"
        elif score >= 0.4:
            label = "moderate_dependency_edge"
        else:
            label = "low_dependency_edge"
        bottleneck_edges.append({"edge_id": edge_id, "source": src, "target": dst, "bottleneck_score": score, "diagnostic_label": label})
    bottleneck_edges = sorted(bottleneck_edges, key=lambda e: (e["source"], e["target"], e["edge_id"]))

    failure_modes: List[str] = []
    if is_empty:
        failure_modes.append("empty_topology")
    if missing_nodes:
        failure_modes.append("missing_nodes")
    if missing_edges:
        failure_modes.append("missing_edges")
    is_disconnected = len(node_ids) > 1 and any(len(_reachable_from(n, adjacency)) == 1 for n in node_ids)
    if is_disconnected:
        failure_modes.append("disconnected_topology")
    if path_count == 0:
        failure_modes.append("no_paths_detected")
    if route_redundancy_score < 0.6 and path_count > 0:
        failure_modes.append("single_route_dependency")
    if any(n["diagnostic_label"] == "bottleneck_node" for n in bottleneck_nodes):
        failure_modes.append("node_bottleneck_detected")
    if any(e["diagnostic_label"] == "bottleneck_edge" for e in bottleneck_edges):
        failure_modes.append("edge_bottleneck_detected")
    if edge_path_consistency_score < 1.0 and edges:
        failure_modes.append("incomplete_path_metadata")
    if trace_continuity_score < 0.5:
        failure_modes.append("weak_trace_continuity")
    if not failure_modes:
        failure_modes.append("none_detected")
    failure_modes = sorted(set(failure_modes))

    labels: List[str] = []
    if is_empty:
        labels.append("empty_topology")
    if path_count == 0:
        labels.append("no_transmission_paths")
    if is_disconnected:
        labels.append("disconnected_paths")
    if any(x in failure_modes for x in ["node_bottleneck_detected", "edge_bottleneck_detected"]):
        labels.append("bottleneck_dominated")
    if route_redundancy_score < 0.6:
        labels.append("weak_route_redundancy")
    if edge_path_consistency_score < 1.0 and edges:
        labels.append("inconsistent_path_edges")
    if trace_continuity_score < 0.5:
        labels.append("weak_trace_continuity")
    if not labels:
        labels.append("path_integrity_stable")
    labels = sorted(set(labels))

    status = "success"
    if missing_nodes or missing_edges:
        status = "insufficient_structure"
    elif labels != ["path_integrity_stable"]:
        status = "completed_with_findings"

    diagnostics = {
        "node_count": len(nodes), "edge_count": len(edges), "path_count": path_count,
        "bottleneck_node_count": sum(1 for n in bottleneck_nodes if n["diagnostic_label"] == "bottleneck_node"),
        "bottleneck_edge_count": sum(1 for e in bottleneck_edges if e["diagnostic_label"] == "bottleneck_edge"),
        "failure_mode_count": len(failure_modes), "is_empty": is_empty, "is_disconnected": is_disconnected,
    }

    result = {
        "status": status,
        "path_integrity_score": path_integrity_score,
        "path_components": component_scores,
        "path_integrity_labels": labels,
        "path_diagnostics": path_diagnostics,
        "bottleneck_nodes": bottleneck_nodes,
        "bottleneck_edges": bottleneck_edges,
        "path_failure_modes": failure_modes,
        "diagnostics": diagnostics,
        "explanation": f"Transmission path integrity completed: status={status}; path_integrity={path_integrity_score}; primary_label={labels[0]}; bottlenecks={diagnostics['bottleneck_node_count'] + diagnostics['bottleneck_edge_count']}; failure_modes={len(failure_modes)}.",
    }
    result["checksum"] = stable_checksum(result, prefix="tier6c")
    return result
