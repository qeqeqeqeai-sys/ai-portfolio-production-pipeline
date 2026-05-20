"""Tier 4C deterministic causal path extraction."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

from .structural_simulation import clamp_normalized_score
from .topology_hashing import normalize_for_replay


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def extract_causal_paths(corridors: Iterable[Dict[str, Any]], max_depth: int = 3) -> List[Dict[str, Any]]:
    edges = sorted(corridors, key=lambda c: (str(c.get("source_node_id", "")), str(c.get("target_node_id", ""))))
    adjacency: Dict[str, List[Tuple[str, Dict[str, Any]]]] = {}
    for e in edges:
        adjacency.setdefault(str(e.get("source_node_id", "")), []).append((str(e.get("target_node_id", "")), e))

    all_paths: List[Dict[str, Any]] = []

    def dfs(node: str, path_nodes: List[str], path_edges: List[Dict[str, Any]], depth: int) -> None:
        if depth >= max_depth:
            return
        for nxt, edge in adjacency.get(node, []):
            if nxt in path_nodes:
                continue
            next_nodes = path_nodes + [nxt]
            next_edges = path_edges + [edge]
            stress = max((_to_float(e.get("stress", 0.0)) for e in next_edges), default=0.0)
            suppression = max((_to_float(e.get("suppression", 0.0)) for e in next_edges), default=0.0)
            cascade = max((1.0 if str(e.get("state", "")) == "failed" else _to_float(e.get("cascade", 0.0)) for e in next_edges), default=0.0)
            deterioration = max((_to_float(e.get("deterioration", 0.0)) for e in next_edges), default=0.0)
            if suppression >= 0.6:
                path_type = "suppression"
            elif cascade >= 0.6:
                path_type = "failure"
            elif deterioration >= 0.5 or stress >= 0.55:
                path_type = "amplification"
            elif suppression > 0.0 and deterioration < 0.25:
                path_type = "recovery"
            else:
                path_type = "neutral"
            impact = clamp_normalized_score(0.40 * stress + 0.25 * deterioration + 0.20 * cascade - 0.15 * suppression)
            all_paths.append({"path": next_nodes, "path_type": path_type, "impact_score": impact, "depth": len(next_edges)})
            dfs(nxt, next_nodes, next_edges, depth + 1)

    for start in sorted(adjacency.keys()):
        dfs(start, [start], [], 0)

    dedup: Dict[Tuple[str, ...], Dict[str, Any]] = {}
    for p in all_paths:
        key = tuple(p["path"])
        if key not in dedup or p["impact_score"] > dedup[key]["impact_score"]:
            dedup[key] = p
    ranked = sorted(dedup.values(), key=lambda p: (-p["impact_score"], p["path_type"], "->".join(p["path"])))
    return normalize_for_replay(ranked)
