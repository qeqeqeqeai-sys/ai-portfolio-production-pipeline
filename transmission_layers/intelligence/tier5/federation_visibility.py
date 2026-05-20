from __future__ import annotations

from typing import Any

from .federation_common import clamp_score
from .federation_observability_signatures import observability_checksum


def federation_visibility_diagnostics(systems: list[dict[str, Any]], bridges: list[dict[str, Any]]) -> dict[str, Any]:
    system_ids = sorted(str(s.get("system_id", s.get("id", ""))) for s in systems)
    connected = {str(b.get("source", "")) for b in bridges} | {str(b.get("target", "")) for b in bridges}
    covered = sum(1 for sid in system_ids if sid and sid in connected)
    total = len(system_ids)
    score = clamp_score((covered / total) if total else 0.0)
    gap = clamp_score(1.0 - score)
    result = {"federation_visibility_score": score, "federation_visibility_gap_score": gap}
    result["federation_visibility_checksum"] = observability_checksum(result, "tier5e_visibility")
    return result
