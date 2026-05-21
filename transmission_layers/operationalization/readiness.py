"""Deterministic manifest-readiness reporting for Operationalization O1D."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .validators import validate_run_manifest


def _sorted_strings(values: list[str]) -> list[str]:
    return sorted(str(v) for v in values)


def _mapping_indicates_false(value: Any, keys: tuple[str, ...]) -> bool:
    if not isinstance(value, Mapping):
        return False
    for key in keys:
        if key in value and value.get(key) is False:
            return True
    return False


def _mapping_indicates_bad_status(value: Any, keys: tuple[str, ...], bad_values: tuple[str, ...]) -> bool:
    if not isinstance(value, Mapping):
        return False
    for key in keys:
        if key in value:
            normalized = str(value.get(key)).strip().lower()
            if normalized in bad_values:
                return True
    return False




def _is_artifact_inventory_invalid(manifest: dict[str, Any]) -> bool:
    inventory = manifest.get("artifact_inventory")
    if not isinstance(inventory, list):
        return False
    for item in inventory:
        if isinstance(item, Mapping):
            if item.get("is_valid") is False:
                return True
            status = str(item.get("status", "")).strip().lower()
            if status in {"invalid", "failed", "error"}:
                return True
    return False


def _is_checksum_inventory_invalid(manifest: dict[str, Any]) -> bool:
    inventory = manifest.get("checksum_inventory")
    if not isinstance(inventory, Mapping):
        return False
    if inventory.get("is_valid") is False:
        return True
    status = str(inventory.get("status", "")).strip().lower()
    return status in {"invalid", "failed", "error"}


def _is_replay_incompatible(manifest: dict[str, Any]) -> bool:
    replay = manifest.get("replay_compatibility")
    return _mapping_indicates_false(replay, ("is_replay_compatible", "replay_compatible", "compatible")) or _mapping_indicates_bad_status(
        replay,
        ("status", "compatibility_status", "compatibility"),
        ("incompatible", "not_compatible", "false", "invalid"),
    )


def _is_chronology_invalid(manifest: dict[str, Any]) -> bool:
    chronology = manifest.get("chronology_summary")
    return _mapping_indicates_false(chronology, ("is_valid", "chronology_valid", "is_chronology_valid")) or _mapping_indicates_bad_status(
        chronology,
        ("status", "chronology_status", "validation_status"),
        ("invalid", "not_valid", "failed", "error"),
    )


def assess_manifest_readiness(manifest: dict) -> dict:
    """Classify manifest readiness deterministically using O1C validator output."""
    validation = validate_run_manifest(manifest)

    blocking_reasons: list[str] = []
    classification = "ready"

    if not validation["is_valid"]:
        classification = "invalid_manifest"
        blocking_reasons.extend(validation["errors"])
    elif _is_replay_incompatible(manifest):
        classification = "replay_incompatible"
        blocking_reasons.append("replay_compatibility:incompatible")
    elif _is_artifact_inventory_invalid(manifest):
        classification = "artifact_inventory_invalid"
        blocking_reasons.append("artifact_inventory:invalid")
    elif _is_checksum_inventory_invalid(manifest):
        classification = "checksum_inventory_invalid"
        blocking_reasons.append("checksum_inventory:invalid")
    elif _is_chronology_invalid(manifest):
        classification = "chronology_invalid"
        blocking_reasons.append("chronology_summary:invalid")

    blocking_reasons = _sorted_strings(blocking_reasons)
    warnings = _sorted_strings(validation.get("warnings", []))
    is_ready = classification == "ready"

    return {
        "is_ready": is_ready,
        "readiness_status": "ready" if is_ready else "not_ready",
        "readiness_classification": classification,
        "validation_status": validation["validation_status"],
        "blocking_reasons": blocking_reasons,
        "warnings": warnings,
    }


def build_manifest_validation_report(manifest: dict) -> dict:
    """Build deterministic validation+readiness report for a manifest."""
    validation = validate_run_manifest(manifest)
    readiness = assess_manifest_readiness(manifest)

    return {
        "report_status": "success",
        "validation": validation,
        "readiness": readiness,
        "summary": {
            "validation_status": validation["validation_status"],
            "readiness_status": readiness["readiness_status"],
            "readiness_classification": readiness["readiness_classification"],
            "error_count": len(validation["errors"]),
            "warning_count": len(validation["warnings"]),
            "blocking_reason_count": len(readiness["blocking_reasons"]),
        },
    }
