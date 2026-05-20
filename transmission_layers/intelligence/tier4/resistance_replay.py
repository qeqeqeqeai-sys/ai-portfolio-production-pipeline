from __future__ import annotations

from typing import Any

from .resistance_signatures import compute_resistance_replay_checksum


def replay_resistance_timeline(states: list[dict[str, Any]], window_size: int = 20) -> dict[str, Any]:
    bounded = max(0, min(int(window_size), 200))
    timeline = [{"step": i, **dict(s)} for i, s in enumerate(states[:bounded])]
    out = {"resistance_timeline": timeline, "resistance_replay_window_size": len(timeline), "chronology_preserved": all(timeline[i]["step"] < timeline[i + 1]["step"] for i in range(len(timeline)-1))}
    out["resistance_replay_checksum"] = compute_resistance_replay_checksum(out)
    return out
