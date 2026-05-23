"""B4 injected-client Supabase repository for deterministic snapshot persistence."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json

from .b4_snapshot_persistence_contract import resolve_b4_table_names
from .b4_snapshot_persistence_validator import validate_b4_snapshot_persistence_input


def _stable_checksum(payload: object) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode("utf-8")).hexdigest()


def _derive_snapshot_identity(envelope: dict) -> dict:
    snapshot = envelope["b1_snapshot_payload"]
    snapshot_date = snapshot.get("snapshot_date", "")
    universe_id = snapshot.get("universe_id", "B1_FIXED_UNIVERSE")
    snapshot_checksum = snapshot.get("deterministic_checksum", _stable_checksum(snapshot))
    b3_checksum = envelope.get("deterministic_checksum", "")
    identity = f"{snapshot_date}|{snapshot_checksum}|{b3_checksum}|{universe_id}"
    return {
        "snapshot_date": snapshot_date,
        "snapshot_checksum": snapshot_checksum,
        "b3_checksum": b3_checksum,
        "universe_id": universe_id,
        "persistence_identity": _stable_checksum(identity),
    }


def build_snapshot_persistence_record(envelope: dict) -> dict:
    frozen = deepcopy(envelope)
    identity = _derive_snapshot_identity(frozen)
    return {
        **identity,
        "b3_decision": frozen.get("b3_decision"),
        "snapshot_payload": deepcopy(frozen.get("b1_snapshot_payload")),
        "certification_payload": deepcopy(frozen.get("b1_certification_payload")),
        "degraded_visibility": deepcopy(frozen.get("degraded_visibility", {})),
        "b2_candidate_reference": deepcopy(frozen.get("b2_candidate_reference", {})),
        "replay_contract": deepcopy(frozen.get("replay_contract", {})),
        "forbidden_capability_contract": deepcopy(frozen.get("forbidden_capability_contract", {})),
    }


def build_snapshot_audit_record(envelope: dict) -> dict:
    frozen = deepcopy(envelope)
    identity = _derive_snapshot_identity(frozen)
    return {
        **identity,
        "audit_stage": "B4_CONTROLLED_PERSISTENCE",
        "b3_validation_summary": deepcopy(frozen.get("b3_validation_summary", {})),
        "b3_mapping_summary": deepcopy(frozen.get("b3_mapping_summary", {})),
        "b1_certification_payload": deepcopy(frozen.get("b1_certification_payload", {})),
    }


def build_snapshot_fragility_record(envelope: dict) -> dict:
    frozen = deepcopy(envelope)
    identity = _derive_snapshot_identity(frozen)
    return {**identity, "fragility_payload": deepcopy(frozen.get("b1_fragility_payload", {}))}


def persist_certified_market_snapshot(client, envelope: dict, table_names: dict | None = None, allow_degraded: bool = False) -> dict:
    validation = validate_b4_snapshot_persistence_input(envelope, allow_degraded=allow_degraded)
    normalized = validation["normalized_envelope"]
    snapshot_checksum = normalized.get("b1_snapshot_payload", {}).get("deterministic_checksum")
    b3_checksum = normalized.get("deterministic_checksum")
    result = {
        "persistence_status": "BLOCKED_PERSISTENCE_INVALID",
        "decision": normalized.get("b3_decision"),
        "written_tables": [],
        "blocked_reason": ",".join(validation["errors"]) if validation["errors"] else None,
        "snapshot_checksum": snapshot_checksum,
        "b3_checksum": b3_checksum,
        "allow_degraded": allow_degraded,
        "record_counts": {"snapshots": 0, "audit": 0, "fragility": 0},
        "replay_contract": deepcopy(normalized.get("replay_contract", {})),
        "forbidden_capability_contract": deepcopy(normalized.get("forbidden_capability_contract", {})),
    }
    if validation["status"] != "READY":
        if "degraded_not_allowed" in validation["errors"]:
            result["persistence_status"] = "BLOCKED_DEGRADED_NOT_ALLOWED"
        return result

    tables = resolve_b4_table_names(table_names)
    snapshot_record = build_snapshot_persistence_record(normalized)
    audit_record = build_snapshot_audit_record(normalized)
    fragility_record = build_snapshot_fragility_record(normalized)

    try:
        client.table(tables["snapshots"]).upsert(snapshot_record, on_conflict="persistence_identity").execute()
        client.table(tables["audit"]).upsert(audit_record, on_conflict="persistence_identity").execute()
        client.table(tables["fragility"]).upsert(fragility_record, on_conflict="persistence_identity").execute()
    except Exception as exc:  # deterministic blocking surface
        result["persistence_status"] = "BLOCKED_REPOSITORY_ERROR"
        result["blocked_reason"] = f"repository_error:{exc.__class__.__name__}"
        return result

    result["persistence_status"] = (
        "PERSISTED_CERTIFIED_SNAPSHOT"
        if normalized.get("b3_decision") == "CERTIFIED_SNAPSHOT_READY"
        else "PERSISTED_DEGRADED_SNAPSHOT"
    )
    result["written_tables"] = [tables["snapshots"], tables["audit"], tables["fragility"]]
    result["blocked_reason"] = None
    result["record_counts"] = {"snapshots": 1, "audit": 1, "fragility": 1}
    return result
