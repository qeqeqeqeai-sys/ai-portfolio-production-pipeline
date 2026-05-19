"""Tier 4B deterministic temporal replay utilities."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List
import hashlib
import json

from .structural_simulation import clamp_normalized_score
from .topology_drift import analyze_topology_drift



def load_structural_snapshot(snapshot_payload: Dict[str, Any]) -> Dict[str, Any]:
    return json.loads(json.dumps(snapshot_payload, sort_keys=True))



def compare_snapshots(previous: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
    prev_prop = previous.get("propagation_summary", {})
    cur_prop = current.get("propagation_summary", {})
    prev_health = str(previous.get("simulation_health_state", ""))
    cur_health = str(current.get("simulation_health_state", ""))

    prev_failed = {k for k, v in previous.get("corridor_metrics", {}).items() if str(v.get("state")) == "failed"}
    cur_failed = {k for k, v in current.get("corridor_metrics", {}).items() if str(v.get("state")) == "failed"}

    return {
        "classification_changed": prev_health != cur_health,
        "previous_health_state": prev_health,
        "current_health_state": cur_health,
        "resilience_delta": round(float(cur_prop.get("resilience_degradation_score", 0.0)) - float(prev_prop.get("resilience_degradation_score", 0.0)), 6),
        "overload_delta": round(float(cur_prop.get("chokepoint_overload_score", 0.0)) - float(prev_prop.get("chokepoint_overload_score", 0.0)), 6),
        "propagated_stress_delta": round(float(cur_prop.get("propagated_stress_score", 0.0)) - float(prev_prop.get("propagated_stress_score", 0.0)), 6),
        "newly_failed_corridors": sorted(cur_failed - prev_failed),
        "recovered_corridors": sorted(prev_failed - cur_failed),
        "invariant_regression": sorted(set(current.get("invariant_validation", {}).get("failed_invariants", [])) - set(previous.get("invariant_validation", {}).get("failed_invariants", []))),
    }



def replay_structural_timeline(snapshots: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    ordered = sorted([load_structural_snapshot(s) for s in snapshots], key=lambda s: (str(s.get("run_date", "")), str(s.get("simulation_run_id", ""))))
    transitions = []
    recurring_failed_counter: Dict[str, int] = {}
    recurring_chokepoint_counter: Dict[str, int] = {}

    for idx in range(1, len(ordered)):
        prev = ordered[idx - 1]
        cur = ordered[idx]
        diff = compare_snapshots(prev, cur)
        drift = analyze_topology_drift(prev, cur)
        transitions.append({"from": prev.get("run_date"), "to": cur.get("run_date"), "diff": diff, "drift": drift})

    for snapshot in ordered:
        for cid, data in snapshot.get("corridor_metrics", {}).items():
            if str(data.get("state", "")) == "failed":
                recurring_failed_counter[cid] = recurring_failed_counter.get(cid, 0) + 1
        for nid, metrics in snapshot.get("node_metrics", {}).items():
            if float(metrics.get("is_overloaded", 0.0)) >= 1.0:
                recurring_chokepoint_counter[nid] = recurring_chokepoint_counter.get(nid, 0) + 1

    recurring_failed = sorted([k for k, v in recurring_failed_counter.items() if v >= 2])
    recurring_chokepoints = sorted([k for k, v in recurring_chokepoint_counter.items() if v >= 2])

    health_states = [str(s.get("simulation_health_state", "mixed")) for s in ordered]
    resilience_series = [float(s.get("propagation_summary", {}).get("resilience_degradation_score", 0.0)) for s in ordered]
    propagated_series = [float(s.get("propagation_summary", {}).get("propagated_stress_score", 0.0)) for s in ordered]

    structural_persistence = clamp_normalized_score(1.0 - (len({s.get("topology_hash", "") for s in ordered}) - 1) / max(1, len(ordered) - 1)) if ordered else 1.0
    resilience_persistence = clamp_normalized_score(1.0 - (max(resilience_series) - min(resilience_series) if resilience_series else 0.0))
    propagation_volatility = clamp_normalized_score(max(propagated_series) - min(propagated_series) if propagated_series else 0.0)
    replay_consistency = clamp_normalized_score(1.0 if len(ordered) <= 1 else sum(1 for i in range(1, len(ordered)) if compare_snapshots(ordered[i - 1], ordered[i]) == compare_snapshots(ordered[i - 1], ordered[i])) / (len(ordered) - 1))
    topology_drift_score = clamp_normalized_score(sum(t["drift"]["topology_drift_score"] for t in transitions) / len(transitions) if transitions else 0.0)
    corridor_stability = clamp_normalized_score(1.0 - (len(recurring_failed) / max(1, len({c for s in ordered for c in s.get('corridor_metrics', {}).keys()}))))

    diagnostics = {
        "replay_window_size": len(ordered),
        "structural_memory_entries": len(ordered),
        "recurring_cascade_detected": bool(recurring_failed or recurring_chokepoints),
        "topology_drift_detected": any(t["drift"]["topology_changed"] for t in transitions),
        "replay_consistency_valid": replay_consistency == 1.0,
        "replay_checksum": hashlib.sha256(json.dumps({"health_states": health_states, "transitions": transitions}, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
    }

    return {
        "ordered_run_dates": [s.get("run_date") for s in ordered],
        "health_state_timeline": health_states,
        "transitions": transitions,
        "recurring_failed_corridors": recurring_failed,
        "recurring_chokepoints": recurring_chokepoints,
        "temporal_stability_metrics": {
            "structural_persistence_score": structural_persistence,
            "corridor_stability_score": corridor_stability,
            "replay_consistency_score": replay_consistency,
            "resilience_persistence_score": resilience_persistence,
            "propagation_volatility_score": propagation_volatility,
            "topology_drift_score": topology_drift_score,
        },
        "operational_diagnostics": diagnostics,
    }
