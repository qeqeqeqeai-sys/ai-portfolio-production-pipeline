from __future__ import annotations

from typing import Any

from .federation_common import clamp_score
from .federation_observability_signatures import observability_checksum


def federation_replay_observability_diagnostics(replay_snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(replay_snapshots, key=lambda s: str(s.get("snapshot_id", "")))
    serializable = sum(1 for s in ordered if isinstance(s, dict))
    score = clamp_score((serializable / len(ordered)) if ordered else 0.0)
    result = {"federation_replay_observability_score": score}
    result["federation_replay_observability_checksum"] = observability_checksum(result, "tier5e_replay_observability")
    return result
