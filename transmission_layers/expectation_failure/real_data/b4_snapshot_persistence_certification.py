"""B4 certification surface for persistence readiness."""

from __future__ import annotations

from copy import deepcopy

from .b4_snapshot_persistence_validator import validate_b4_snapshot_persistence_input


def certify_b4_snapshot_persistence_readiness(envelope: dict, allow_degraded: bool = False) -> dict:
    frozen = deepcopy(envelope)
    validation = validate_b4_snapshot_persistence_input(frozen, allow_degraded=allow_degraded)
    if validation["status"] == "BLOCKED":
        return {
            "decision": "BLOCKED_PERSISTENCE_INVALID",
            "errors": validation["errors"],
            "replay_contract": deepcopy(frozen.get("replay_contract", {})),
            "checksums": {
                "b3_checksum": frozen.get("deterministic_checksum"),
                "snapshot_checksum": frozen.get("b1_snapshot_payload", {}).get("deterministic_checksum"),
            },
        }
    return {
        "decision": "DEGRADED_PERSISTENCE_READY" if frozen.get("b3_decision") == "DEGRADED_SNAPSHOT_READY" else "CERTIFIED_PERSISTENCE_READY",
        "errors": [],
        "replay_contract": deepcopy(frozen.get("replay_contract", {})),
        "checksums": {
            "b3_checksum": frozen.get("deterministic_checksum"),
            "snapshot_checksum": frozen.get("b1_snapshot_payload", {}).get("deterministic_checksum"),
        },
    }
