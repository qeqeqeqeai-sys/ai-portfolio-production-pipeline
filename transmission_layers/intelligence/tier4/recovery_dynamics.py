from __future__ import annotations

from typing import Any, Dict, List

from .recovery_decay import compute_recovery_decay
from .recovery_persistence import compute_stabilization_persistence
from .recovery_signatures import compute_recovery_checksum, compute_recovery_signature_checksum


def _bound01(value: float) -> float:
    return max(0.0, min(1.0, round(float(value), 6)))


def compute_recovery_durability(recovery_states: List[Dict[str, Any]]) -> Dict[str, Any]:
    persistence = compute_stabilization_persistence(recovery_states)
    decay = compute_recovery_decay(recovery_states)
    durability = _bound01((persistence["persistence_score"] + (1.0 - decay["relapse_score"])) / 2.0)
    return {
        "recovery_durability_score": durability,
        "recovery_persistence_score": persistence["persistence_score"],
        "relapse_resistance": _bound01(1.0 - decay["relapse_score"]),
    }


def compare_recovery_durability(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    delta = round(float(a.get("recovery_durability_score", 0.0)) - float(b.get("recovery_durability_score", 0.0)), 6)
    return {"durability_delta": max(-1.0, min(1.0, delta)), "a_gt_b": delta > 0}


def summarize_recovery_durability(durability: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "recovery_durability_score": _bound01(durability.get("recovery_durability_score", 0.0)),
        "recovery_persistence_score": _bound01(durability.get("recovery_persistence_score", 0.0)),
    }


def compute_recovery_trajectory(recovery_states: List[Dict[str, Any]]) -> Dict[str, Any]:
    state_seq = []
    for s in recovery_states:
        state_seq.append(
            {
                "resilience": _bound01(float(s.get("resilience", 0.0))),
                "overload": _bound01(float(s.get("overload", 1.0))),
                "fragmentation": _bound01(float(s.get("fragmentation", 1.0))),
            }
        )
    persistence = compute_stabilization_persistence(state_seq)
    decay = compute_recovery_decay(state_seq)
    durability = compute_recovery_durability(state_seq)
    score = _bound01((durability["recovery_durability_score"] + persistence["persistence_score"]) / 2.0)
    trajectory = {
        "recovery_state_sequence": state_seq,
        "recovery_stability_score": persistence["persistence_score"],
        "bounded_recovery_score": score,
        "recovery_duration": len(state_seq),
        "persistence_duration": persistence["stabilization_duration"],
        "relapse_detected": decay["relapse_detected"],
        "recovery_persistence_score": persistence["persistence_score"],
        "recovery_durability_score": durability["recovery_durability_score"],
        "dominant_decay_factor": decay["dominant_decay_factor"],
        "recovery_consistency_valid": True,
        "recovery_replay_window_size": len(state_seq),
    }
    trajectory["recovery_trajectory_id"] = compute_recovery_signature_checksum({"recovery_state_sequence": state_seq})[:16]
    trajectory["recovery_checksum"] = compute_recovery_checksum(trajectory)
    trajectory["recovery_signature_checksum"] = compute_recovery_signature_checksum(trajectory)
    return trajectory


def summarize_recovery_trajectory(trajectory: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "recovery_trajectory_id": str(trajectory.get("recovery_trajectory_id", "")),
        "bounded_recovery_score": _bound01(trajectory.get("bounded_recovery_score", 0.0)),
        "recovery_duration": int(trajectory.get("recovery_duration", 0)),
        "persistence_duration": int(trajectory.get("persistence_duration", 0)),
        "relapse_detected": bool(trajectory.get("relapse_detected", False)),
        "recovery_checksum": str(trajectory.get("recovery_checksum", "")),
    }


def compare_recovery_trajectories(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    delta = round(float(a.get("bounded_recovery_score", 0.0)) - float(b.get("bounded_recovery_score", 0.0)), 6)
    return {
        "bounded_recovery_score_delta": max(-1.0, min(1.0, delta)),
        "same_checksum": a.get("recovery_checksum") == b.get("recovery_checksum"),
        "same_relapse_status": bool(a.get("relapse_detected", False)) == bool(b.get("relapse_detected", False)),
    }
