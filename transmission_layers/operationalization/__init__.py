"""Operationalization helpers for deterministic serialization and checksums."""

from .serialization import stable_checksum, stable_serialize
from .readiness import assess_manifest_readiness, build_manifest_validation_report
from .validators import validate_run_manifest
from .export_envelope import build_manifest_export_envelope, build_dry_run_operational_report
from .export_persistence import build_export_filename, persist_manifest_export_envelope
from .export_verification import load_manifest_export_envelope, verify_manifest_export_envelope
from .audit_summary import build_operational_audit_summary
from .supervisor_review import build_operationalization_supervisor_review
from .replay_contract import assess_replay_contract, build_replay_plan_skeleton
from .replay_supervisor_review import build_replay_supervisor_review
from .replay_guardrails import build_replay_engine_guardrails
from .replay_preflight import build_replay_engine_preflight
from .replay_dry_run import execute_replay_dry_run
from .replay_observability_closure import (
    build_replay_integrity_diagnostics,
    build_replay_observability_summary,
    run_replay_observability_closure,
)


def run_operationalization_cli_smoke(export_dir, *, overwrite=False):
    from .cli_smoke import run_operationalization_cli_smoke as _run

    return _run(export_dir, overwrite=overwrite)


__all__ = [
    "stable_serialize",
    "stable_checksum",
    "validate_run_manifest",
    "assess_manifest_readiness",
    "build_manifest_validation_report",
    "build_manifest_export_envelope",
    "build_dry_run_operational_report",
    "build_export_filename",
    "persist_manifest_export_envelope",
    "load_manifest_export_envelope",
    "verify_manifest_export_envelope",
    "build_operational_audit_summary",
    "run_operationalization_cli_smoke",
    "build_operationalization_supervisor_review",
    "assess_replay_contract",
    "build_replay_plan_skeleton",
    "build_replay_supervisor_review",
    "build_replay_engine_guardrails",
    "build_replay_engine_preflight",
    "execute_replay_dry_run",
    "build_replay_integrity_diagnostics",
    "build_replay_observability_summary",
    "run_replay_observability_closure",
]
