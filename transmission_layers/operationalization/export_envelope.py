"""Deterministic dry-run export envelope for Operationalization O1E."""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from typing import Any

from .readiness import build_manifest_validation_report


def _is_list_like(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _is_mapping_like(value: Any) -> bool:
    return isinstance(value, Mapping)


def build_manifest_export_envelope(manifest: dict) -> dict:
    """Build deterministic export-shaped envelope around O1D validation output."""
    validation_report = build_manifest_validation_report(manifest)
    manifest_copy = copy.deepcopy(manifest)

    artifact_inventory = manifest_copy.get("artifact_inventory")
    checksum_inventory = manifest_copy.get("checksum_inventory")

    artifact_count = len(artifact_inventory) if _is_list_like(artifact_inventory) else 0
    checksum_entry_count = len(checksum_inventory) if _is_mapping_like(checksum_inventory) else 0

    export_ready = bool(validation_report["readiness"]["is_ready"])

    export_summary = {
        "validation_status": validation_report["summary"]["validation_status"],
        "readiness_status": validation_report["summary"]["readiness_status"],
        "readiness_classification": validation_report["summary"]["readiness_classification"],
        "error_count": validation_report["summary"]["error_count"],
        "warning_count": validation_report["summary"]["warning_count"],
        "blocking_reason_count": validation_report["summary"]["blocking_reason_count"],
        "artifact_count": artifact_count,
        "checksum_entry_count": checksum_entry_count,
    }

    return {
        "export_status": "dry_run",
        "export_ready": export_ready,
        "envelope_type": "manifest_export",
        "manifest": manifest_copy,
        "validation_report": validation_report,
        "export_summary": export_summary,
    }


def build_dry_run_operational_report(manifest: dict) -> dict:
    """Build deterministic dry-run operational report for manifest export."""
    export_envelope = build_manifest_export_envelope(manifest)

    summary = {
        "export_status": export_envelope["export_status"],
        "export_ready": export_envelope["export_ready"],
        "validation_status": export_envelope["export_summary"]["validation_status"],
        "readiness_status": export_envelope["export_summary"]["readiness_status"],
        "readiness_classification": export_envelope["export_summary"]["readiness_classification"],
        "artifact_count": export_envelope["export_summary"]["artifact_count"],
        "checksum_entry_count": export_envelope["export_summary"]["checksum_entry_count"],
        "warning_count": export_envelope["export_summary"]["warning_count"],
        "blocking_reason_count": export_envelope["export_summary"]["blocking_reason_count"],
    }

    return {
        "report_status": "success",
        "operation_mode": "dry_run",
        "operation_type": "manifest_export",
        "export_envelope": export_envelope,
        "summary": summary,
    }
