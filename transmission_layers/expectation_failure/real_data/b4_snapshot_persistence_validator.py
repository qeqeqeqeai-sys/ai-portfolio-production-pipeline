"""B4 validation and eligibility gates for B3-certified snapshot persistence."""

from __future__ import annotations

from copy import deepcopy

from .b4_snapshot_persistence_contract import (
    B4_ALLOWED_B3_DECISIONS,
    B4_BLOCKED_B3_DECISION,
    B4_FORBIDDEN_CAPABILITY_CONTRACT,
)


def validate_b4_snapshot_persistence_input(envelope: dict, allow_degraded: bool = False) -> dict:
    frozen = deepcopy(envelope)
    errors: list[str] = []

    if not isinstance(frozen, dict):
        return {"status": "BLOCKED", "errors": ["malformed_envelope"], "normalized_envelope": {}}

    b3_decision = frozen.get("b3_decision")
    if b3_decision == B4_BLOCKED_B3_DECISION:
        errors.append("blocked_b3_decision")
    if b3_decision not in B4_ALLOWED_B3_DECISIONS and b3_decision != B4_BLOCKED_B3_DECISION:
        errors.append("unknown_b3_decision")
    if b3_decision == "DEGRADED_SNAPSHOT_READY" and not allow_degraded:
        errors.append("degraded_not_allowed")

    if not frozen.get("deterministic_checksum"):
        errors.append("missing_b3_checksum")
    if not frozen.get("replay_contract"):
        errors.append("missing_replay_contract")

    forbidden = frozen.get("forbidden_capability_contract")
    if not isinstance(forbidden, dict):
        errors.append("missing_forbidden_capability_contract")
    else:
        required_disallowed_keys = {"trading", "prediction", "target_prices", "optimization", "autonomous_notifications"}
        for key in required_disallowed_keys:
            if forbidden.get(key) != "disallowed":
                errors.append(f"forbidden_capability_violation:{key}")
                break

    b1_payload = frozen.get("b1_snapshot_payload")
    b1_fragility = frozen.get("b1_fragility_payload")
    b1_cert = frozen.get("b1_certification_payload")
    if not isinstance(b1_payload, dict):
        errors.append("missing_b1_snapshot_payload")
    if not isinstance(b1_fragility, dict):
        errors.append("missing_b1_fragility_payload")
    if not isinstance(b1_cert, dict):
        errors.append("missing_b1_certification_payload")

    status = "READY" if not errors else "BLOCKED"
    return {"status": status, "errors": errors, "normalized_envelope": frozen}
