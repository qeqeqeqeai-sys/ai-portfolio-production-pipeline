"""Tier 4C deterministic structural causal lineage tracing."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List
import hashlib

from .causal_paths import extract_causal_paths
from .topology_hashing import canonical_json_bytes, normalize_for_hashing, normalize_for_replay


def _sorted_unique(values: Iterable[str]) -> List[str]:
    return sorted({str(v) for v in values if str(v).strip()})


def trace_causal_lineage(node_attribution: Iterable[Dict[str, Any]], corridor_attribution: Iterable[Dict[str, Any]], max_depth: int = 3) -> Dict[str, Any]:
    nodes = list(node_attribution)
    corridors = list(corridor_attribution)
    root_cause_nodes = [n["node_id"] for n in sorted(nodes, key=lambda n: (int(n.get("attribution_rank", 999999)), str(n.get("node_id", ""))))[:3]]
    root_cause_corridors = [c["corridor_id"] for c in sorted(corridors, key=lambda c: (int(c.get("attribution_rank", 999999)), str(c.get("corridor_id", ""))))[:3]]
    extracted_paths = extract_causal_paths(corridors, max_depth=max_depth)
    amplification_paths = [p["path"] for p in extracted_paths if p["path_type"] == "amplification"]
    suppression_paths = [p["path"] for p in extracted_paths if p["path_type"] == "suppression"]
    downstream = _sorted_unique(node for path in [p["path"] for p in extracted_paths] for node in path[1:])
    lineage = normalize_for_replay(
        {
            "root_cause_nodes": root_cause_nodes,
            "root_cause_corridors": root_cause_corridors,
            "amplification_paths": amplification_paths,
            "suppression_paths": suppression_paths,
            "affected_downstream_nodes": downstream,
            "causal_depth": min(max_depth, max((len(p["path"]) - 1 for p in extracted_paths), default=0)),
            "explanations": _sorted_unique(
                [
                    f"node_{n['node_id']} ranked {n['attribution_rank']} because {n.get('attribution_reason', 'baseline structural contribution')}."
                    for n in sorted(nodes, key=lambda x: (int(x.get("attribution_rank", 999999)), str(x.get("node_id", ""))))[:3]
                ]
                + [
                    f"corridor_{c['corridor_id']} ranked {c['attribution_rank']} because {c.get('attribution_reason', 'baseline corridor contribution')}."
                    for c in sorted(corridors, key=lambda x: (int(x.get("attribution_rank", 999999)), str(x.get("corridor_id", ""))))[:3]
                ]
            ),
            "causal_paths": extracted_paths,
        }
    )
    lineage["lineage_checksum"] = hashlib.sha256(canonical_json_bytes(normalize_for_hashing(lineage))).hexdigest()
    return normalize_for_replay(lineage)


def trace_corridor_lineage(corridor_id: str, lineage: Dict[str, Any]) -> Dict[str, Any]:
    corridor = str(corridor_id)
    matching = [p for p in lineage.get("causal_paths", []) if any("->".join(p["path"][i : i + 2]) == corridor for i in range(max(0, len(p["path"]) - 1)))]
    return normalize_for_replay({"corridor_id": corridor, "paths": matching, "path_count": len(matching)})


def trace_node_lineage(node_id: str, lineage: Dict[str, Any]) -> Dict[str, Any]:
    node = str(node_id)
    matching = [p for p in lineage.get("causal_paths", []) if node in p.get("path", [])]
    return normalize_for_replay({"node_id": node, "paths": matching, "path_count": len(matching)})
