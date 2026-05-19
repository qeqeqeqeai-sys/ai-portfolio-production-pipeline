"""Tier 4B deterministic topology drift analysis."""
from __future__ import annotations

from typing import Any, Dict, List

from .structural_simulation import clamp_normalized_score


def _sorted_unique(values: List[str]) -> List[str]:
    return sorted({str(v) for v in values if str(v).strip()})


def analyze_topology_drift(previous: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
    prev_nodes = set(previous.get("node_structural_metrics", {}).keys())
    cur_nodes = set(current.get("node_structural_metrics", {}).keys())
    prev_corridors = previous.get("corridor_structural_metrics", {})
    cur_corridors = current.get("corridor_structural_metrics", {})

    added_nodes = _sorted_unique(list(cur_nodes - prev_nodes))
    removed_nodes = _sorted_unique(list(prev_nodes - cur_nodes))
    added_corridors = _sorted_unique(list(set(cur_corridors) - set(prev_corridors)))
    removed_corridors = _sorted_unique(list(set(prev_corridors) - set(cur_corridors)))

    transitions: List[str] = []
    for corridor_id in sorted(set(prev_corridors) & set(cur_corridors)):
        p_state = str(prev_corridors[corridor_id].get("state", ""))
        c_state = str(cur_corridors[corridor_id].get("state", ""))
        if p_state != c_state:
            transitions.append(f"{corridor_id}:{p_state}->{c_state}")

    prev_failed = {k for k, v in prev_corridors.items() if str(v.get("state")) == "failed"}
    cur_failed = {k for k, v in cur_corridors.items() if str(v.get("state")) == "failed"}
    prev_overloaded = {n for n, m in previous.get("node_structural_metrics", {}).items() if float(m.get("is_overloaded", 0.0)) >= 1.0}
    cur_overloaded = {n for n, m in current.get("node_structural_metrics", {}).items() if float(m.get("is_overloaded", 0.0)) >= 1.0}

    fragmentation_delta = round(float(current.get("overload", 0.0)) - float(previous.get("overload", 0.0)), 6)
    suppression_delta = round(float(current.get("propagation_summaries", {}).get("suppression", 0.0)) - float(previous.get("propagation_summaries", {}).get("suppression", 0.0)), 6)

    drift_events = len(added_nodes) + len(removed_nodes) + len(added_corridors) + len(removed_corridors) + len(transitions)
    denom = max(1, len(prev_nodes | cur_nodes) + len(set(prev_corridors) | set(cur_corridors)))
    drift_score = clamp_normalized_score(drift_events / denom)

    return {
        "topology_changed": bool(drift_events),
        "node_additions": added_nodes,
        "node_removals": removed_nodes,
        "corridor_additions": added_corridors,
        "corridor_removals": removed_corridors,
        "corridor_state_transitions": _sorted_unique(transitions),
        "chokepoint_emergence": _sorted_unique(list(cur_overloaded - prev_overloaded)),
        "resilience_deterioration": round(float(current.get("resilience", 0.0)) - float(previous.get("resilience", 0.0)), 6),
        "fragmentation_changes": fragmentation_delta,
        "suppression_expansion": suppression_delta,
        "cascading_failure_recurrence": bool(prev_failed and cur_failed and bool(prev_failed & cur_failed)),
        "topology_drift_score": drift_score,
    }
