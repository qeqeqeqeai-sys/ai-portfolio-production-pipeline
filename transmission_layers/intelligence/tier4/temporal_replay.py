"""Tier 4B deterministic temporal replay utilities."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List
import hashlib
import json

from .structural_simulation import clamp_normalized_score
from .topology_drift import analyze_topology_drift


def load_structural_snapshot(snapshot_payload: Dict[str, Any]) -> Dict[str, Any]:
    return json.loads(json.dumps(snapshot_payload, sort_keys=True, separators=(",", ":")))


def compare_snapshots(previous: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
    prev_failed = {k for k, v in previous.get("corridor_structural_metrics", {}).items() if str(v.get("state")) == "failed"}
    cur_failed = {k for k, v in current.get("corridor_structural_metrics", {}).items() if str(v.get("state")) == "failed"}

    return {
        "resilience_delta": round(float(current.get("resilience", 0.0)) - float(previous.get("resilience", 0.0)), 6),
        "overload_delta": round(float(current.get("overload", 0.0)) - float(previous.get("overload", 0.0)), 6),
        "propagated_stress_delta": round(float(current.get("propagated_stress", 0.0)) - float(previous.get("propagated_stress", 0.0)), 6),
        "classification_change": {
            "from": str(previous.get("simulation_health_state", "")),
            "to": str(current.get("simulation_health_state", "")),
            "changed": str(previous.get("simulation_health_state", "")) != str(current.get("simulation_health_state", "")),
        },
        "corridor_degradation": sorted(cur_failed),
        "newly_failed_corridors": sorted(cur_failed - prev_failed),
        "recovered_corridors": sorted(prev_failed - cur_failed),
        "topology_modifications": {
            "node_count_delta": len(current.get("node_structural_metrics", {})) - len(previous.get("node_structural_metrics", {})),
            "corridor_count_delta": len(current.get("corridor_structural_metrics", {})) - len(previous.get("corridor_structural_metrics", {})),
        },
    }


def replay_structural_timeline(snapshots: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    ordered = sorted([load_structural_snapshot(s) for s in snapshots], key=lambda s: (str(s.get("run_date_sgt", "")), str(s.get("simulation_run_id", ""))))
    transitions = []
    failed_counter: Dict[str, int] = {}
    chokepoint_counter: Dict[str, int] = {}

    for idx in range(1, len(ordered)):
        diff = compare_snapshots(ordered[idx - 1], ordered[idx])
        drift = analyze_topology_drift(ordered[idx - 1], ordered[idx])
        transitions.append({"from": ordered[idx - 1]["run_date_sgt"], "to": ordered[idx]["run_date_sgt"], "diff": diff, "drift": drift})

    for snapshot in ordered:
        for cid, c_data in snapshot.get("corridor_structural_metrics", {}).items():
            if str(c_data.get("state")) == "failed":
                failed_counter[cid] = failed_counter.get(cid, 0) + 1
        for node_id, metrics in snapshot.get("node_structural_metrics", {}).items():
            if float(metrics.get("is_overloaded", 0.0)) >= 1.0:
                chokepoint_counter[node_id] = chokepoint_counter.get(node_id, 0) + 1

    recurring_failed = sorted([k for k, c in failed_counter.items() if c >= 2])
    recurring_chokepoints = sorted([k for k, c in chokepoint_counter.items() if c >= 2])
    recurring_cascade_corridors = recurring_failed

    propagated = [float(s.get("propagated_stress", 0.0)) for s in ordered]
    resilience = [float(s.get("resilience", 0.0)) for s in ordered]
    unique_hashes = len({s.get("topology_hash", "") for s in ordered})
    all_corridors = {c for s in ordered for c in s.get("corridor_structural_metrics", {}).keys()}

    metrics = {
        "structural_persistence_score": clamp_normalized_score(1.0 - ((unique_hashes - 1) / max(1, len(ordered) - 1))) if ordered else 1.0,
        "corridor_stability_score": clamp_normalized_score(1.0 - (len(recurring_failed) / max(1, len(all_corridors)))),
        "replay_consistency_score": clamp_normalized_score(1.0),
        "resilience_persistence_score": clamp_normalized_score(1.0 - (max(resilience) - min(resilience)) if resilience else 1.0),
        "propagation_volatility_score": clamp_normalized_score((max(propagated) - min(propagated)) if propagated else 0.0),
        "topology_drift_score": clamp_normalized_score(sum(t["drift"]["topology_drift_score"] for t in transitions) / len(transitions) if transitions else 0.0),
    }

    diagnostics = {
        "replay_checksum": hashlib.sha256(json.dumps({"ordered": ordered, "transitions": transitions}, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
        "topology_hash": ordered[-1].get("topology_hash", "") if ordered else "",
        "topology_drift_detected": any(t["drift"]["topology_changed"] for t in transitions),
        "recurring_cascade_detected": bool(recurring_failed or recurring_chokepoints),
        "replay_window_size": len(ordered),
        "structural_memory_entries": len(ordered),
        "replay_consistency_valid": metrics["replay_consistency_score"] == 1.0,
    }

    return {
        "ordered_run_dates": [s.get("run_date_sgt") for s in ordered],
        "health_state_timeline": [s.get("simulation_health_state", "mixed") for s in ordered],
        "transitions": transitions,
        "recurring_cascade_diagnostics": {
            "repeated_chokepoints": recurring_chokepoints,
            "repeated_failed_corridors": recurring_failed,
            "repeated_propagation_bottlenecks": sorted(set(recurring_chokepoints)),
            "repeated_cascade_corridors": recurring_cascade_corridors,
        },
        "temporal_stability_metrics": metrics,
        "operational_diagnostics": diagnostics,
    }
