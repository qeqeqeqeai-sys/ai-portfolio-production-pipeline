from __future__ import annotations

from typing import Any, Dict, List

from .recovery_signatures import compute_recovery_replay_checksum


def replay_structural_recovery(recovery_states: List[Dict[str, Any]], window_size: int = 20) -> Dict[str, Any]:
    bounded = max(0, min(int(window_size), 200))
    sequence = [dict(s) for s in recovery_states[:bounded]]
    timeline = [{"step": i, **state} for i, state in enumerate(sequence)]
    out = {
        "recovery_timeline": timeline,
        "recovery_replay_window_size": len(timeline),
        "chronology_preserved": all(timeline[i]["step"] < timeline[i + 1]["step"] for i in range(len(timeline) - 1)),
    }
    out["recovery_replay_checksum"] = compute_recovery_replay_checksum(out)
    return out


def compare_recovery_replays(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "same_checksum": a.get("recovery_replay_checksum") == b.get("recovery_replay_checksum"),
        "same_window": int(a.get("recovery_replay_window_size", 0)) == int(b.get("recovery_replay_window_size", 0)),
        "window_delta": int(a.get("recovery_replay_window_size", 0)) - int(b.get("recovery_replay_window_size", 0)),
    }


def summarize_recovery_replay(replay: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "recovery_replay_window_size": int(replay.get("recovery_replay_window_size", 0)),
        "recovery_replay_checksum": str(replay.get("recovery_replay_checksum", "")),
        "chronology_preserved": bool(replay.get("chronology_preserved", True)),
    }
