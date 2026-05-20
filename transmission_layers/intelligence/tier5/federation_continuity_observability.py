from __future__ import annotations

from typing import Any

from .federation_common import clamp_score
from .federation_observability_signatures import observability_checksum


def federation_continuity_observability_diagnostics(replay_snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    snapshot_ids = [str(s.get("snapshot_id", "")) for s in replay_snapshots]
    score = clamp_score(1.0 if snapshot_ids == sorted(snapshot_ids) else 0.0)
    result = {"federation_continuity_observability_score": score}
    result["federation_continuity_observability_checksum"] = observability_checksum(result, "tier5e_continuity_observability")
    return result
