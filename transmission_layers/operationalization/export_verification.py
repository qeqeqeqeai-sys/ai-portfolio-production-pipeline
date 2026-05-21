"""Deterministic load and verification for persisted export envelopes (Operationalization O1G)."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from .export_persistence import build_export_filename


def load_manifest_export_envelope(export_path: str | Path) -> dict:
    """Load persisted manifest export envelope JSON from disk using UTF-8."""
    path = Path(export_path)
    payload_text = path.read_text(encoding="utf-8")
    return json.loads(payload_text)


def verify_manifest_export_envelope(export_path: str | Path) -> dict:
    """Verify deterministic structure and integrity of persisted export envelope."""
    path = Path(export_path)
    envelope = load_manifest_export_envelope(path)

    errors: list[str] = []
    warnings: list[str] = []

    manifest = envelope.get("manifest") if isinstance(envelope, Mapping) else None
    validation_report = envelope.get("validation_report") if isinstance(envelope, Mapping) else None
    export_summary_raw = envelope.get("export_summary") if isinstance(envelope, Mapping) else None

    envelope_type_valid = isinstance(envelope, Mapping) and envelope.get("envelope_type") == "manifest_export"
    export_status_valid = isinstance(envelope, Mapping) and envelope.get("export_status") == "dry_run"
    manifest_present = isinstance(manifest, Mapping)
    validation_report_present = isinstance(validation_report, Mapping)
    export_summary_present = isinstance(export_summary_raw, Mapping)

    filename_matches_manifest_checksum = False
    if manifest_present:
        filename_matches_manifest_checksum = path.name == build_export_filename(manifest)

    envelope_ready_matches_readiness = False
    if validation_report_present:
        readiness = validation_report.get("readiness")
        if isinstance(readiness, Mapping):
            envelope_ready_matches_readiness = envelope.get("export_ready") == readiness.get("is_ready")

    integrity_check = {
        "envelope_type_valid": envelope_type_valid,
        "export_status_valid": export_status_valid,
        "manifest_present": manifest_present,
        "filename_matches_manifest_checksum": filename_matches_manifest_checksum,
        "envelope_ready_matches_readiness": envelope_ready_matches_readiness,
        "validation_report_present": validation_report_present,
        "export_summary_present": export_summary_present,
    }

    if not envelope_type_valid:
        errors.append("invalid_envelope_type")
    if not export_status_valid:
        errors.append("invalid_export_status")
    if not manifest_present:
        errors.append("missing_manifest")
    if not filename_matches_manifest_checksum:
        errors.append("filename_manifest_checksum_mismatch")
    if not envelope_ready_matches_readiness:
        errors.append("export_ready_readiness_mismatch")
    if not validation_report_present:
        errors.append("missing_validation_report")
    if not export_summary_present:
        errors.append("missing_export_summary")

    errors = sorted(errors)
    warnings = sorted(warnings)

    is_verified = all(integrity_check.values())
    verification_status = "valid" if is_verified else "invalid"

    export_summary = export_summary_raw if export_summary_present else {}

    return {
        "verification_status": verification_status,
        "is_verified": is_verified,
        "export_path": str(path),
        "export_filename": path.name,
        "errors": errors,
        "warnings": warnings,
        "integrity_check": integrity_check,
        "export_summary": export_summary,
    }
