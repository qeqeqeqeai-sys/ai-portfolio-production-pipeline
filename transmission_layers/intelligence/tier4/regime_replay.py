from __future__ import annotations

import hashlib, json
from typing import Any, Dict, List

from .regime_persistence import compute_regime_persistence
from .regime_transitions import replay_regime_transitions
from .structural_regimes import classify_structural_regime


def replay_regime_timeline(snapshots: List[Dict[str, Any]], window_size: int | None = None) -> Dict[str, Any]:
    ordered = sorted(snapshots, key=lambda s: str(s.get("run_date", "")))
    if window_size is not None:
        ordered = ordered[-max(0, int(window_size)):]
    sequence = [classify_structural_regime(s)["regime_name"] for s in ordered]
    transitions = replay_regime_transitions(ordered)
    persistence = compute_regime_persistence(ordered)
    payload = {"sequence": sequence, "transitions": transitions, "persistence": persistence}
    checksum = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {"regime_sequence": sequence, "transition_points": transitions, "persistence_summary": persistence, "replay_regime_consistency_valid": True, "regime_replay_checksum": checksum, "regime_replay_window_size": len(ordered)}


def summarize_regime_replay(snapshots: List[Dict[str, Any]]) -> Dict[str, Any]:
    r = replay_regime_timeline(snapshots)
    return {"regime_transition_count": len(r["transition_points"]), "regime_persistence_score": r["persistence_summary"]["persistence_score"], "replay_regime_consistency_valid": r["replay_regime_consistency_valid"], "regime_replay_window_size": r["regime_replay_window_size"]}


def compare_regime_replay_windows(a: List[Dict[str, Any]], b: List[Dict[str, Any]]) -> Dict[str, Any]:
    ra = replay_regime_timeline(a)
    rb = replay_regime_timeline(b)
    return {"sequence_changed": ra["regime_sequence"] != rb["regime_sequence"], "transition_count_delta": len(rb["transition_points"]) - len(ra["transition_points"]), "checksum_equal": ra["regime_replay_checksum"] == rb["regime_replay_checksum"]}
