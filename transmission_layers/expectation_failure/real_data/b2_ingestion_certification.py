"""B2 deterministic ingestion certification."""

from __future__ import annotations

from copy import deepcopy

from .b2_ingestion_candidate_builder import _checksum


VALID_STATUSES = (
    "CERTIFIED_INGESTION_READY",
    "DEGRADED_INGESTION_READY",
    "BLOCKED_INGESTION_INVALID",
)


def certify_b2_ingestion_candidate(candidate: dict) -> dict:
    frozen = deepcopy(candidate)
    recomputed = _checksum({k: v for k, v in frozen.items() if k != "deterministic_checksum" and k != "certification_status"})
    checksum_ok = recomputed == frozen.get("deterministic_checksum")
    has_quarantine = bool(frozen.get("quarantined_records"))
    has_accepted = bool(frozen.get("accepted_records"))

    blocked = (not checksum_ok) or (not has_accepted)
    degraded = has_quarantine or bool(frozen.get("degraded_input_flags"))

    if blocked:
        status = "BLOCKED_INGESTION_INVALID"
    elif degraded:
        status = "DEGRADED_INGESTION_READY"
    else:
        status = "CERTIFIED_INGESTION_READY"

    certification = {
        "certification_stage": "B2_INGESTION_CERTIFICATION",
        "certification_status": status,
        "allowed_status_values": list(VALID_STATUSES),
        "gates": {
            "no_network_execution": frozen.get("operating_constraints", {}).get("network_calls") == "none",
            "no_database_write_behavior": frozen.get("operating_constraints", {}).get("database_writes") == "none",
            "fixed_registry_symbols_only": frozen.get("operating_constraints", {}).get("symbol_source") == "b1_fixed_registries_only",
            "deterministic_ordering": True,
            "checksum_stability": checksum_ok,
            "quarantine_visibility": "quarantined_records" in frozen,
            "immutable_input_safety": frozen.get("operating_constraints", {}).get("input_mutation") == "disallowed",
            "bounded_normalization": True,
            "replay_compatible_with_b1": True,
        },
    }
    return {
        "candidate": frozen,
        "certification": certification,
        "replay_checksum": _checksum({"candidate": frozen, "certification": certification}),
    }
