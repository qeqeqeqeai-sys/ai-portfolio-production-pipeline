"""Tier 4B deterministic topology drift analysis."""
from __future__ import annotations

from typing import Any, Dict, List

from .structural_simulation import clamp_normalized_score



def _stable(items: List[str]) -> List[str]:
    return sorted({str(x) for x in items if str(x).strip()})



def analyze_topology_drift(previous: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
    prev_nodes = set(previous.get("node_metrics", {}).keys())
    cur_nodes = set(current.get("node_metrics", {}).keys())
    prev_corr = previous.get("corridor_metrics", {})
    cur_corr = current.get("corridor_metrics", {})

    new_nodes = _stable(list(cur_nodes - prev_nodes))
    removed_nodes = _stable(list(prev_nodes - cur_nodes))
    new_corridors = _stable(list(set(cur_corr.keys()) - set(prev_corr.keys())))
    removed_corridors = _stable(list(set(prev_corr.keys()) - set(cur_corr.keys())))

    corridor_state_changes = []
    for cid in sorted(set(prev_corr.keys()) & set(cur_corr.keys())):
        prev_state = str(prev_corr[cid].get("state", ""))
        cur_state = str(cur_corr[cid].get("state", ""))
        if prev_state != cur_state:
            corridor_state_changes.append(f"{cid}:{prev_state}->{cur_state}")

    prev_overload = set([n for n, v in previous.get("node_metrics", {}).items() if v.get("is_overloaded", 0.0) >= 1.0])
    cur_overload = set([n for n, v in current.get("node_metrics", {}).items() if v.get("is_overloaded", 0.0) >= 1.0])
    new_chokepoints = _stable(list(cur_overload - prev_overload))

    resilience_delta = round(
        float(current.get("propagation_summary", {}).get("resilience_degradation_score", 0.0))
        - float(previous.get("propagation_summary", {}).get("resilience_degradation_score", 0.0)),
        6,
    )
    topology_changed = bool(new_nodes or removed_nodes or new_corridors or removed_corridors or corridor_state_changes)
    drift_events = len(new_nodes) + len(removed_nodes) + len(new_corridors) + len(removed_corridors) + len(corridor_state_changes)
    total_elements = max(1, len(prev_nodes | cur_nodes) + len(set(prev_corr.keys()) | set(cur_corr.keys())))
    topology_drift_score = clamp_normalized_score(drift_events / total_elements)

    return {
        "topology_changed": topology_changed,
        "new_nodes": new_nodes,
        "removed_nodes": removed_nodes,
        "new_corridors": new_corridors,
        "removed_corridors": removed_corridors,
        "corridor_state_changes": _stable(corridor_state_changes),
        "new_chokepoints": new_chokepoints,
        "resilience_delta": resilience_delta,
        "topology_drift_score": topology_drift_score,
    }
