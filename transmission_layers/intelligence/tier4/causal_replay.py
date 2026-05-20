"""Tier 4C deterministic causal replay over structural snapshots."""
from __future__ import annotations

from typing import Any, Dict
import hashlib

from .attribution_metrics import compute_attribution_metrics
from .causal_lineage import trace_causal_lineage
from .influence_attribution import compute_structural_influence_summary
from .topology_hashing import canonical_json_bytes, normalize_for_hashing, normalize_for_replay


def compare_causal_snapshots(previous: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
    prev_summary = compute_structural_influence_summary(previous.get("node_metrics", []), previous.get("corridor_metrics", []))
    cur_summary = compute_structural_influence_summary(current.get("node_metrics", []), current.get("corridor_metrics", []))

    prev_nodes = {n["node_id"]: n for n in prev_summary["node_attribution"]}
    cur_nodes = {n["node_id"]: n for n in cur_summary["node_attribution"]}
    rank_changes = []
    for node_id in sorted(set(prev_nodes.keys()) | set(cur_nodes.keys())):
        prev_rank = int(prev_nodes.get(node_id, {}).get("attribution_rank", 0))
        cur_rank = int(cur_nodes.get(node_id, {}).get("attribution_rank", 0))
        if prev_rank != cur_rank:
            rank_changes.append({"node_id": node_id, "previous_rank": prev_rank, "current_rank": cur_rank})

    prev_roots = {n["node_id"] for n in prev_summary["node_attribution"][:3]}
    cur_roots = {n["node_id"] for n in cur_summary["node_attribution"][:3]}
    prev_chokepoints = {n["node_id"] for n in prev_summary["node_attribution"] if n.get("overload_contribution", 0.0) >= 0.6}
    cur_chokepoints = {n["node_id"] for n in cur_summary["node_attribution"] if n.get("overload_contribution", 0.0) >= 0.6}

    lineage = trace_causal_lineage(cur_summary["node_attribution"], cur_summary["corridor_attribution"], max_depth=3)
    shift_detected = bool(rank_changes or (prev_roots != cur_roots))
    metrics = compute_attribution_metrics(cur_summary["node_attribution"], cur_summary["corridor_attribution"], int(lineage.get("causal_depth", 0)), shift_detected)

    return normalize_for_replay(
        {
            "previous_health_state": str(previous.get("health_state", "")),
            "current_health_state": str(current.get("health_state", "")),
            "attribution_rank_changes": rank_changes,
            "new_root_causes": sorted(cur_roots - prev_roots),
            "resolved_root_causes": sorted(prev_roots - cur_roots),
            "changed_chokepoints": sorted((cur_chokepoints - prev_chokepoints) | (prev_chokepoints - cur_chokepoints)),
            "causal_transition_summary": summarize_causal_transition(previous, current, rank_changes),
            "lineage": lineage,
            "metrics": metrics,
        }
    )


def summarize_causal_transition(previous: Dict[str, Any], current: Dict[str, Any], rank_changes: Any) -> str:
    prev_state = str(previous.get("health_state", "unknown"))
    cur_state = str(current.get("health_state", "unknown"))
    direction = "deteriorated" if prev_state != cur_state and cur_state in {"stressed", "degraded", "failed", "fragile", "cascading_failure"} else "shifted"
    return f"health state {direction} from {prev_state} to {cur_state}; attribution rank changes={len(rank_changes)}"


def replay_causal_influence(previous: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
    comparison = compare_causal_snapshots(previous, current)
    payload = normalize_for_hashing(comparison)
    comparison["replay_checksum"] = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
    comparison["operational_diagnostics"] = {
        "causal_replay_checksum": comparison["replay_checksum"],
        "root_cause_count": len(comparison.get("lineage", {}).get("root_cause_nodes", [])),
        "causal_path_count": len(comparison.get("lineage", {}).get("causal_paths", [])),
        "attribution_shift_detected": bool(comparison.get("attribution_rank_changes")),
        "lineage_depth_max": int(comparison.get("lineage", {}).get("causal_depth", 0)),
        "influence_concentration_score": comparison.get("metrics", {}).get("influence_concentration_score", 0.0),
    }
    return normalize_for_replay(comparison)
