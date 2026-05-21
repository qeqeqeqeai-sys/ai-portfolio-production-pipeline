"""Deterministic manifest validators for Operationalization O1C."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

_REQUIRED_FIELDS: tuple[str, ...] = (
    "run_id",
    "run_type",
    "tier_scope",
    "generated_at_sgt",
    "schema_version",
    "execution_status",
    "artifact_inventory",
    "checksum_inventory",
    "replay_compatibility",
    "chronology_summary",
)

_LEGACY_STRING_ALLOWED: dict[str, tuple[str, ...]] = {
    "replay_compatibility": ("deterministic_payload_only",),
    "chronology_summary": ("unspecified",),
}


def _is_list_like(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _is_mapping_like(value: Any) -> bool:
    return isinstance(value, Mapping)


def _is_mapping_like_or_legacy_string(field: str, value: Any) -> bool:
    if _is_mapping_like(value):
        return True
    if isinstance(value, str):
        return value in _LEGACY_STRING_ALLOWED.get(field, ())
    return False


def validate_run_manifest(manifest: dict) -> dict:
    """Validate O1B run-manifest structure deterministically without side effects."""
    errors: list[str] = []
    warnings: list[str] = []

    present_fields = set(manifest.keys())
    missing_fields = [field for field in _REQUIRED_FIELDS if field not in present_fields]
    required_fields_present = not missing_fields

    for field in missing_fields:
        errors.append(f"missing_required_field:{field}")

    extra_fields = sorted(present_fields.difference(_REQUIRED_FIELDS))
    for field in extra_fields:
        warnings.append(f"unknown_field:{field}")

    artifact_inventory_valid = "artifact_inventory" in manifest and _is_list_like(manifest.get("artifact_inventory"))
    if "artifact_inventory" in manifest and not artifact_inventory_valid:
        errors.append("invalid_type:artifact_inventory:list_like_required")

    checksum_inventory_valid = "checksum_inventory" in manifest and _is_mapping_like(manifest.get("checksum_inventory"))
    if "checksum_inventory" in manifest and not checksum_inventory_valid:
        errors.append("invalid_type:checksum_inventory:mapping_like_required")

    replay_compatibility_valid = "replay_compatibility" in manifest and _is_mapping_like_or_legacy_string(
        "replay_compatibility", manifest.get("replay_compatibility")
    )
    if "replay_compatibility" in manifest and not replay_compatibility_valid:
        errors.append("invalid_type:replay_compatibility:mapping_like_required")

    chronology_summary_valid = "chronology_summary" in manifest and _is_mapping_like_or_legacy_string(
        "chronology_summary", manifest.get("chronology_summary")
    )
    if "chronology_summary" in manifest and not chronology_summary_valid:
        errors.append("invalid_type:chronology_summary:mapping_like_required")

    errors = sorted(errors)
    warnings = sorted(warnings)
    is_valid = (
        required_fields_present
        and artifact_inventory_valid
        and checksum_inventory_valid
        and replay_compatibility_valid
        and chronology_summary_valid
        and not errors
    )

    return {
        "is_valid": is_valid,
        "validation_status": "valid" if is_valid else "invalid",
        "errors": errors,
        "warnings": warnings,
        "required_fields_present": required_fields_present,
        "artifact_inventory_valid": artifact_inventory_valid,
        "checksum_inventory_valid": checksum_inventory_valid,
        "replay_compatibility_valid": replay_compatibility_valid,
        "chronology_summary_valid": chronology_summary_valid,
    }
