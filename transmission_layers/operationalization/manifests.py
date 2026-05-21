"""Deterministic operational run manifest model (Operationalization O1B)."""

from __future__ import annotations

from typing import Any

from transmission_layers.operationalization.serialization import stable_checksum


_MANIFEST_SCHEMA_VERSION = "o1b.v1"
_DEFAULT_EXECUTION_STATUS = "pending"
_DEFAULT_REPLAY_COMPATIBILITY = "deterministic_payload_only"
_DEFAULT_CHRONOLOGY_SUMMARY = "unspecified"


def _copy_mapping(value: dict[str, Any] | None) -> dict[str, Any]:
    if value is None:
        return {}
    return {k: v for k, v in value.items()}


def _copy_sequence(value: list[Any] | tuple[Any, ...] | None) -> list[Any]:
    if value is None:
        return []
    return [item for item in value]


def build_run_manifest(
    *,
    run_id: str,
    run_type: str,
    tier_scope: str,
    generated_at_sgt: str,
    schema_version: str = _MANIFEST_SCHEMA_VERSION,
    execution_status: str = _DEFAULT_EXECUTION_STATUS,
    artifact_inventory: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None = None,
    checksum_inventory: dict[str, str] | None = None,
    replay_compatibility: str = _DEFAULT_REPLAY_COMPATIBILITY,
    chronology_summary: str = _DEFAULT_CHRONOLOGY_SUMMARY,
) -> dict[str, Any]:
    """Construct a deterministic run manifest from explicit inputs.

    No implicit clock lookup is performed; callers must provide generated_at_sgt.
    """
    return {
        "run_id": run_id,
        "run_type": run_type,
        "tier_scope": tier_scope,
        "generated_at_sgt": generated_at_sgt,
        "schema_version": schema_version,
        "execution_status": execution_status,
        "artifact_inventory": _copy_sequence(artifact_inventory),
        "checksum_inventory": _copy_mapping(checksum_inventory),
        "replay_compatibility": replay_compatibility,
        "chronology_summary": chronology_summary,
    }


def manifest_checksum(manifest: dict[str, Any]) -> str:
    """Return deterministic checksum token for a run manifest."""
    return stable_checksum(manifest, prefix="manifest")


def empty_manifest(
    *,
    run_id: str,
    run_type: str,
    tier_scope: str,
    generated_at_sgt: str,
    schema_version: str = _MANIFEST_SCHEMA_VERSION,
    execution_status: str = _DEFAULT_EXECUTION_STATUS,
    replay_compatibility: str = _DEFAULT_REPLAY_COMPATIBILITY,
    chronology_summary: str = _DEFAULT_CHRONOLOGY_SUMMARY,
) -> dict[str, Any]:
    """Construct a valid-shaped manifest with empty inventories."""
    return build_run_manifest(
        run_id=run_id,
        run_type=run_type,
        tier_scope=tier_scope,
        generated_at_sgt=generated_at_sgt,
        schema_version=schema_version,
        execution_status=execution_status,
        artifact_inventory=[],
        checksum_inventory={},
        replay_compatibility=replay_compatibility,
        chronology_summary=chronology_summary,
    )
