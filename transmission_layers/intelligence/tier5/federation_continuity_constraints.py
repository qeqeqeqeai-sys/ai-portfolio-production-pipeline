from __future__ import annotations

from typing import Any

from .federation_common import clamp_score


def federation_continuity_constraint_diagnostics(replay_snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(replay_snapshots, key=lambda s: str(s.get("snapshot_id", s.get("step", ""))))
    if len(ordered) <= 1:
        return {"federation_continuity_constraint_score": 1.0, "federation_governance_stability_score": 1.0}
    drift = []
    for i in range(1, len(ordered)):
        a = set(sorted(str(x) for x in ordered[i - 1].get("boundary_weaknesses", [])))
        b = set(sorted(str(x) for x in ordered[i].get("boundary_weaknesses", [])))
        u = len(a | b)
        drift.append(0.0 if u == 0 else len(a ^ b) / u)
    avg_drift = sum(drift) / len(drift)
    return {
        "federation_continuity_constraint_score": clamp_score(1.0 - avg_drift),
        "federation_governance_stability_score": clamp_score(1.0 - avg_drift),
    }
