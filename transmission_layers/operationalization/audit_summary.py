"""Deterministic operational audit summary orchestration (Operationalization O1H)."""

from __future__ import annotations

from pathlib import Path

from .export_envelope import build_manifest_export_envelope
from .export_persistence import persist_manifest_export_envelope
from .export_verification import verify_manifest_export_envelope
from .readiness import build_manifest_validation_report


def _build_not_applicable_verification(persistence: dict) -> dict:
    return {
        "verification_status": "not_applicable",
        "is_verified": False,
        "export_path": persistence["export_path"],
        "export_filename": persistence["export_filename"],
        "errors": [],
        "warnings": [],
        "integrity_check": {},
        "export_summary": {},
    }


def build_operational_audit_summary(manifest: dict, export_dir: str | Path, *, overwrite: bool = False) -> dict:
    """Build deterministic operational audit summary without replay or scheduling side effects."""
    validation_report = build_manifest_validation_report(manifest)
    export_envelope = build_manifest_export_envelope(manifest)
    persistence = persist_manifest_export_envelope(manifest, export_dir, overwrite=overwrite)

    persistence_status = persistence["persistence_status"]
    if persistence_status in {"written", "skipped_existing"}:
        verification = verify_manifest_export_envelope(persistence["export_path"])
    else:
        verification = _build_not_applicable_verification(persistence)

    audit_summary = {
        "validation_status": validation_report["summary"]["validation_status"],
        "readiness_status": validation_report["summary"]["readiness_status"],
        "readiness_classification": validation_report["summary"]["readiness_classification"],
        "export_status": export_envelope["export_status"],
        "export_ready": export_envelope["export_ready"],
        "persistence_status": persistence_status,
        "verification_status": verification["verification_status"],
        "is_verified": verification["is_verified"],
        "error_count": validation_report["summary"]["error_count"],
        "warning_count": validation_report["summary"]["warning_count"],
        "blocking_reason_count": validation_report["summary"]["blocking_reason_count"],
        "artifact_count": export_envelope["export_summary"]["artifact_count"],
        "checksum_entry_count": export_envelope["export_summary"]["checksum_entry_count"],
    }

    return {
        "audit_status": "success",
        "operation_mode": "deterministic_audit",
        "validation_report": validation_report,
        "export_envelope": export_envelope,
        "persistence": persistence,
        "verification": verification,
        "audit_summary": audit_summary,
    }
