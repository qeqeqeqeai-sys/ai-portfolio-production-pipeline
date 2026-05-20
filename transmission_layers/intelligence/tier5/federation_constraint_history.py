from __future__ import annotations

from typing import Any

from .federation_common import clamp_score


def federation_constraint_history_diagnostics(replay_snapshots: list[dict[str, Any]]) -> dict[str, float]:
    ordered = sorted(replay_snapshots, key=lambda s: str(s.get("snapshot_id", s.get("step", ""))))
    seq = [len(set(sorted(str(x) for x in snap.get("boundary_weaknesses", [])))) for snap in ordered]
    if not seq:
        return {"federation_constraint_recurrence_score": 0.0}
    repeats = sum(1 for i in range(1, len(seq)) if seq[i] == seq[i - 1])
    return {"federation_constraint_recurrence_score": clamp_score(repeats / max(1, len(seq) - 1))}
