from __future__ import annotations

from typing import Any

from .federation_common import clamp_score, mean_bounded
from .federation_resilience_signatures import federation_resilience_checksum


def federation_recovery_paths(contagion_paths: list[dict[str, Any]], replay_snapshots: list[dict[str, Any]]) -> dict[str, float]:
    ordered_paths = sorted(contagion_paths, key=lambda p: (str(p.get("source", "")), str(p.get("target", "")), str(p.get("path_id", ""))))
    recovery_coverage = 0.0 if not ordered_paths else sum(1.0 for p in ordered_paths if bool(p.get("contained", False)) and str(p.get("target", "")) != "") / len(ordered_paths)
    ordered_snaps = sorted(replay_snapshots, key=lambda s: str(s.get("snapshot_id", "")))
    replay_quality = 0.0 if not ordered_snaps else sum(1.0 for s in ordered_snaps if str(s.get("state", "")) != "") / len(ordered_snaps)
    score = mean_bounded([recovery_coverage, replay_quality])
    result = {"federation_recovery_path_score": clamp_score(score)}
    result["federation_recovery_paths_checksum"] = federation_resilience_checksum(result, "tier5g_paths")
    return result
