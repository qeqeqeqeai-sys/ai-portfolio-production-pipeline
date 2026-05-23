"""B3 certification decisioning for deterministic snapshot assembly."""

from __future__ import annotations


def decide_b3_snapshot_assembly(validation_summary: dict) -> str:
    status = validation_summary.get("status")
    if status == "BLOCKED":
        return "BLOCKED_SNAPSHOT_INVALID"
    if status == "DEGRADED":
        return "DEGRADED_SNAPSHOT_READY"
    return "CERTIFIED_SNAPSHOT_READY"
