from __future__ import annotations

from typing import Any

from .federation_common import clamp_score
from .federation_observability_signatures import observability_checksum


def federation_telemetry_diagnostics(replay_snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(replay_snapshots, key=lambda s: str(s.get("snapshot_id", "")))
    populated = sum(1 for s in ordered if len(s.keys()) > 1)
    score = clamp_score((populated / len(ordered)) if ordered else 0.0)
    result = {"federation_telemetry_score": score}
    result["federation_telemetry_checksum"] = observability_checksum(result, "tier5e_telemetry")
    return result
