from __future__ import annotations

from typing import Any

from .fragility_signatures import compute_fragility_replay_checksum


def replay_fragility(fragility_states: list[dict[str, Any]], window_size: int = 20) -> dict[str, Any]:
    bounded = max(0, min(int(window_size), 200))
    sequence = [dict(s) for s in fragility_states[:bounded]]
    timeline = [{"step": i, **state} for i, state in enumerate(sequence)]
    out = {
        "fragility_timeline": timeline,
        "fragility_replay_window_size": len(timeline),
        "chronology_preserved": all(timeline[i]["step"] < timeline[i + 1]["step"] for i in range(len(timeline) - 1)),
        "timeline_start_step": timeline[0]["step"] if timeline else -1,
        "timeline_end_step": timeline[-1]["step"] if timeline else -1,
    }
    out["fragility_replay_checksum"] = compute_fragility_replay_checksum(out)
    return out


def compare_fragility_replays(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    window_a = int(a.get("fragility_replay_window_size", 0))
    window_b = int(b.get("fragility_replay_window_size", 0))
    return {
        "same_checksum": str(a.get("fragility_replay_checksum", "")) == str(b.get("fragility_replay_checksum", "")),
        "same_window": window_a == window_b,
        "window_delta": window_a - window_b,
    }
