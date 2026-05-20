from __future__ import annotations

from typing import Any, Dict, List

from .response_signatures import compute_response_replay_checksum


def replay_structural_response(sequence: List[Dict[str, Any]], window_size: int = 20) -> Dict[str, Any]:
    bounded = max(0, min(int(window_size), 200))
    seq = [dict(x) for x in sequence[:bounded]]
    timeline = [{"step": i, "response_policy_id": str(x.get("response_policy_id", "")), "response_type": str(x.get("response_type", "limited_recovery")), "response_score": round(float(x.get("response_score", 0.0)), 6)} for i, x in enumerate(seq)]
    out = {"response_timeline": timeline, "response_sequence": [x["response_policy_id"] for x in timeline], "response_replay_window_size": len(timeline), "chronology_preserved": all(timeline[i]["step"] < timeline[i + 1]["step"] for i in range(len(timeline) - 1))}
    out["response_replay_checksum"] = compute_response_replay_checksum(out)
    return out


def compare_response_replays(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    return {"same_sequence": a.get("response_sequence", []) == b.get("response_sequence", []), "same_checksum": a.get("response_replay_checksum") == b.get("response_replay_checksum"), "window_size_delta": int(a.get("response_replay_window_size", 0)) - int(b.get("response_replay_window_size", 0))}


def summarize_response_replay(replay: Dict[str, Any]) -> Dict[str, Any]:
    return {"response_replay_checksum": replay.get("response_replay_checksum", ""), "response_replay_window_size": replay.get("response_replay_window_size", 0), "chronology_preserved": bool(replay.get("chronology_preserved", True))}
