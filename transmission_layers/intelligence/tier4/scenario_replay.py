from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List


def _checksum(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def replay_scenario_response(sequence: List[Dict[str, Any]], window_size: int | None = None) -> Dict[str, Any]:
    seq = list(sequence)
    if window_size is not None:
        seq = seq[: max(0, int(window_size))]
    timeline = [{"step": i, "scenario_id": str(x.get("scenario_id", "")), "regime_name": str(x.get("regime_name", "stable")), "impact_score": round(float(x.get("impact_score", 0.0)), 6)} for i, x in enumerate(seq)]
    transitions = [f"{timeline[i-1]['regime_name']}->{timeline[i]['regime_name']}" for i in range(1, len(timeline)) if timeline[i-1]["regime_name"] != timeline[i]["regime_name"]]
    out = {
        "scenario_sequence": [t["scenario_id"] for t in timeline],
        "response_timeline": timeline,
        "regime_transitions_under_scenario": transitions,
        "scenario_persistence_summary": "stable" if not transitions else "transitional",
        "scenario_replay_window_size": len(timeline),
        "replay_consistency_diagnostics": {"chronology_preserved": True, "deterministic_ordering": True},
    }
    out["scenario_replay_checksum"] = _checksum(out)
    return out


def compare_scenario_replay_windows(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "window_a_size": len(a.get("response_timeline", [])),
        "window_b_size": len(b.get("response_timeline", [])),
        "same_sequence": a.get("scenario_sequence", []) == b.get("scenario_sequence", []),
        "same_checksum": a.get("scenario_replay_checksum") == b.get("scenario_replay_checksum"),
    }


def summarize_scenario_replay(replay: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "scenario_replay_checksum": replay.get("scenario_replay_checksum", ""),
        "scenario_replay_window_size": replay.get("scenario_replay_window_size", 0),
        "scenario_persistence_summary": replay.get("scenario_persistence_summary", "stable"),
    }
