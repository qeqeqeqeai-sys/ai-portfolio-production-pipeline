"""Tier 6D deterministic propagation distortion and signal contamination diagnostics."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Set, Tuple

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
    return sorted((dict(n) for n in nodes if isinstance(n, dict)), key=lambda n: str(n.get("node_id", "")))


def _sorted_edges(topology: Dict[str, Any]) -> List[Dict[str, Any]]:
    edges = topology.get("edges", [])
    if not isinstance(edges, list):
        return []

    def _key(e: Dict[str, Any]) -> Tuple[str, str, str]:
        src = str(e.get("source_node_id", ""))
        dst = str(e.get("target_node_id", ""))
        edge_id = str(e.get("edge_id", f"{src}->{dst}"))
        return (src, dst, edge_id)

    return sorted((dict(e) for e in edges if isinstance(e, dict)), key=_key)


def _semantic_bucket(item: Dict[str, Any]) -> str:
    for field in ("role", "category", "label", "type"):
        val = item.get(field)
        if val is not None and str(val).strip() != "":
            return str(val).strip().lower()
    return ""


def assess_propagation_distortion_diagnostics(topology: Dict[str, Any]) -> Dict[str, Any]:
    topology_view = deepcopy(topology) if isinstance(topology, dict) else {}
    nodes = _sorted_nodes(topology_view)
    edges = _sorted_edges(topology_view)

    node_ids = [str(n.get("node_id", "")) for n in nodes]
    node_set = set(node_ids)
    node_by_id = {str(n.get("node_id", "")): n for n in nodes}

    missing_nodes = len(nodes) == 0
    missing_edges = len(edges) == 0
    is_empty = missing_nodes and missing_edges

    adjacency: Dict[str, Set[str]] = {nid: set() for nid in node_ids}
    in_counts: Dict[str, int] = {nid: 0 for nid in node_ids}
    out_counts: Dict[str, int] = {nid: 0 for nid in node_ids}

    edge_diags: List[Dict[str, Any]] = []
    distorted_edge_count = 0
    contradictory_edge_count = 0
    incomplete_edge_count = 0

    for edge in edges:
        src = str(edge.get("source_node_id", ""))
        dst = str(edge.get("target_node_id", ""))
        edge_id = str(edge.get("edge_id", f"{src}->{dst}"))

        eq = _bounded_score(_to_float(edge.get("edge_quality_score"), 0.0))
        suppressed = bool(edge.get("suppressed_for_propagation", False))
        sem_edge = _semantic_bucket(edge)
        sem_src = _semantic_bucket(node_by_id.get(src, {}))
        sem_dst = _semantic_bucket(node_by_id.get(dst, {}))
        sem_mismatch = bool(sem_edge and ((sem_src and sem_edge != sem_src) or (sem_dst and sem_edge != sem_dst)))

        endpoint_missing = src not in node_set or dst not in node_set or src == "" or dst == ""
        contradiction_flag = bool(edge.get("contradictory", False) or edge.get("is_contradictory", False))

        distortion_score = _bounded_score((1.0 - eq) * 0.7 + (0.2 if suppressed else 0.0) + (0.1 if sem_mismatch else 0.0))
        if endpoint_missing:
            label = "incomplete_edge"
            incomplete_edge_count += 1
        elif contradiction_flag:
            label = "contradictory_edge"
            contradictory_edge_count += 1
        elif distortion_score >= 0.70:
            label = "contaminated_edge"
            distorted_edge_count += 1
        elif distortion_score >= 0.45:
            label = "distorted_edge"
            distorted_edge_count += 1
        else:
            label = "clean_edge"

        if src in adjacency and dst in adjacency:
            adjacency[src].add(dst)
            out_counts[src] += 1
            in_counts[dst] += 1

        edge_diags.append({
            "edge_id": edge_id,
            "source": src,
            "target": dst,
            "distortion_score": distortion_score,
            "diagnostic_label": label,
        })

    edge_diags = sorted(edge_diags, key=lambda e: (e["source"], e["target"], e["edge_id"]))

    node_diags: List[Dict[str, Any]] = []
    contaminated_node_count = 0
    for nid in sorted(node_ids):
        incoming = sum(1 for e in edge_diags if e["target"] == nid and e["diagnostic_label"] in {"distorted_edge", "contaminated_edge", "contradictory_edge"})
        outgoing = sum(1 for e in edge_diags if e["source"] == nid and e["diagnostic_label"] in {"distorted_edge", "contaminated_edge", "contradictory_edge"})
        node = node_by_id.get(nid, {})
        has_meta = _semantic_bucket(node) != ""
        contamination_score = _bounded_score((incoming + outgoing) / max(len(edges), 1)) if edges else 0.0
        if (in_counts.get(nid, 0) + out_counts.get(nid, 0)) == 0:
            label = "isolated_node"
        elif not has_meta:
            label = "insufficient_node_metadata"
        elif outgoing > incoming and outgoing >= 2:
            label = "distortion_amplifier_node"
            contaminated_node_count += 1
        elif contamination_score >= 0.25:
            label = "contaminated_node"
            contaminated_node_count += 1
        else:
            label = "clean_node"
        node_diags.append({
            "node_id": nid,
            "contamination_score": contamination_score,
            "incoming_distortion_count": incoming,
            "outgoing_distortion_count": outgoing,
            "diagnostic_label": label,
        })

    path_diags: List[Dict[str, Any]] = []
    for e in edge_diags:
        score = e["distortion_score"]
        if e["diagnostic_label"] == "incomplete_edge":
            plabel = "incomplete_path"
        elif e["diagnostic_label"] == "contradictory_edge":
            plabel = "contradictory_path"
        elif e["diagnostic_label"] in {"distorted_edge", "contaminated_edge"}:
            plabel = "contaminated_path"
        else:
            plabel = "clean_path"
        if len(adjacency.get(e["source"], set())) == 0 or len(adjacency.get(e["target"], set())) == 0:
            if plabel == "clean_path" and len(node_ids) > 2:
                plabel = "fragmented_path"
                score = _bounded_score(max(score, 0.5))
        path_diags.append({"path_id": e["edge_id"], "source": e["source"], "target": e["target"], "contamination_score": score, "diagnostic_label": plabel})
    path_diags = sorted(path_diags, key=lambda p: (p["source"], p["target"], p["path_id"]))

    possible_pairs = len(node_ids) * (len(node_ids) - 1)
    reachable_pairs = sum(len(v) for v in adjacency.values())
    coherence = _bounded_score(reachable_pairs / possible_pairs) if possible_pairs > 0 else 0.0

    complete_edges = sum(1 for e in edges if e.get("edge_quality_score") is not None and e.get("suppressed_for_propagation") is not None)
    consistency = _bounded_score(complete_edges / len(edges)) if edges else 0.0
    distortion_resistance = _bounded_score(1.0 - (distorted_edge_count + contradictory_edge_count + incomplete_edge_count) / max(len(edges), 1)) if edges else 0.0
    containment = _bounded_score(1.0 - contaminated_node_count / max(len(nodes), 1)) if nodes else 0.0
    aligned_nodes = sum(1 for n in nodes if _semantic_bucket(n) != "")
    semantic_alignment = _bounded_score(aligned_nodes / len(nodes)) if nodes else 0.0
    fragmented_paths = sum(1 for p in path_diags if p["diagnostic_label"] == "fragmented_path")
    fragmentation_resistance = _bounded_score(1.0 - fragmented_paths / max(len(path_diags), 1)) if path_diags else 0.0

    components = {
        "signal_consistency_score": consistency,
        "distortion_resistance_score": distortion_resistance,
        "contamination_containment_score": containment,
        "propagation_coherence_score": coherence,
        "semantic_alignment_score": semantic_alignment,
        "fragmentation_resistance_score": fragmentation_resistance,
    }
    propagation_integrity_score = _bounded_score(sum(components.values()) / len(components))

    is_disconnected = len(node_ids) > 1 and (len(edges) == 0 or reachable_pairs < possible_pairs)
    failure_modes: List[str] = []
    if is_empty:
        failure_modes.append("empty_topology")
    if missing_nodes:
        failure_modes.append("missing_nodes")
    if missing_edges:
        failure_modes.append("missing_edges")
    if is_disconnected:
        failure_modes.append("disconnected_topology")
    if distorted_edge_count > 0:
        failure_modes.append("distorted_edges_detected")
    if contaminated_node_count > 0:
        failure_modes.append("contaminated_nodes_detected")
    if contradictory_edge_count > 0:
        failure_modes.append("contradictory_edges_detected")
    if fragmented_paths > 0:
        failure_modes.append("fragmented_propagation_detected")
    if semantic_alignment < 0.5 and nodes:
        failure_modes.append("weak_semantic_alignment")
    if consistency < 1.0 and edges:
        failure_modes.append("incomplete_signal_metadata")
    if not failure_modes:
        failure_modes.append("none_detected")
    failure_modes = sorted(set(failure_modes))

    labels: List[str] = []
    if is_empty:
        labels.append("empty_topology")
    if missing_nodes or missing_edges:
        labels.append("insufficient_propagation_structure")
    if distorted_edge_count > 0:
        labels.append("distorted_signal_flow")
    if contaminated_node_count > 0:
        labels.append("contaminated_transmission")
    if fragmented_paths > 0:
        labels.append("fragmented_propagation")
    if contradictory_edge_count > 0:
        labels.append("contradictory_transmission")
    if semantic_alignment < 0.5 and nodes:
        labels.append("weak_semantic_alignment")
    if not labels:
        labels.append("propagation_integrity_stable")
    labels = sorted(set(labels))

    status = "success"
    if missing_nodes or missing_edges:
        status = "insufficient_structure"
    elif labels != ["propagation_integrity_stable"]:
        status = "completed_with_findings"

    diagnostics = {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "contamination_path_count": len(path_diags),
        "distorted_edge_count": distorted_edge_count,
        "contaminated_node_count": contaminated_node_count,
        "contradictory_edge_count": contradictory_edge_count,
        "failure_mode_count": len(failure_modes),
        "is_empty": is_empty,
        "is_disconnected": is_disconnected,
    }

    result = {
        "status": status,
        "propagation_integrity_score": propagation_integrity_score,
        "distortion_components": components,
        "distortion_labels": labels,
        "edge_distortion_diagnostics": edge_diags,
        "node_contamination_diagnostics": node_diags,
        "contamination_paths": path_diags,
        "distortion_failure_modes": failure_modes,
        "diagnostics": diagnostics,
        "explanation": f"Propagation distortion diagnostics completed: status={status}; propagation_integrity={propagation_integrity_score}; primary_label={labels[0]}; contaminated_nodes={contaminated_node_count}; distorted_edges={distorted_edge_count}; failure_modes={len(failure_modes)}.",
    }
    result["checksum"] = stable_checksum(result, prefix="tier6d")
    return result
