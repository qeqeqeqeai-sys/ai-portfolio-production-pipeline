from __future__ import annotations

from typing import Any

from .persistence_signatures import compute_durability_replay_checksum


def replay_durability_timeline(states: list[dict[str, Any]], window_size: int = 30) -> dict[str, Any]:
    bounded = max(0, min(int(window_size), 365))
    ordered = [dict(x) for x in states[:bounded]]
    timeline = [{"step": i, **state} for i, state in enumerate(ordered)]
    out = {
        "durability_timeline": timeline,
        "durability_replay_window_size": len(timeline),
        "chronology_preserved": all(timeline[i]["step"] < timeline[i + 1]["step"] for i in range(len(timeline) - 1)),
    }
    out["durability_replay_checksum"] = compute_durability_replay_checksum(out)
    return out
