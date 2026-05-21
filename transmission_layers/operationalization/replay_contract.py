"""Deterministic replay contract skeleton over export verification (Operationalization O1K)."""

from __future__ import annotations

from pathlib import Path

from .export_verification import verify_manifest_export_envelope


def assess_replay_contract(export_path: str | Path) -> dict:
    """Assess replay-readiness contract from a verified manifest export envelope."""
    path = Path(export_path)
    verification = verify_manifest_export_envelope(path)

    integrity_check = verification.get("integrity_check", {})
    export_summary = verification.get("export_summary", {})

    replay_contract_checks = {
        "export_verified": verification.get("is_verified") is True,
        "manifest_export_type_valid": integrity_check.get("envelope_type_valid") is True,
        "dry_run_export_status_valid": integrity_check.get("export_status_valid") is True,
        "readiness_ready": export_summary.get("readiness_status") == "ready",
        "validation_valid": export_summary.get("validation_status") == "valid",
    }

    replay_ready = all(replay_contract_checks.values())
    replay_contract_status = "replay_ready" if replay_ready else "not_replay_ready"

    blocking_reasons = sorted(verification.get("errors", []))
    warnings = sorted(verification.get("warnings", []))

    return {
        "replay_contract_status": replay_contract_status,
        "replay_ready": replay_ready,
        "export_path": str(path),
        "export_filename": path.name,
        "verification_status": verification.get("verification_status", "invalid"),
        "blocking_reasons": blocking_reasons,
        "warnings": warnings,
        "replay_contract_checks": replay_contract_checks,
        "export_summary": export_summary,
    }


def build_replay_plan_skeleton(export_path: str | Path) -> dict:
    """Build deterministic replay plan skeleton without executing any replay runtime logic."""
    replay_contract = assess_replay_contract(export_path)
    replay_ready = replay_contract["replay_ready"]

    precheck_status = "available" if replay_ready else "blocked"
    replay_steps = [
        {
            "step_name": "load_export_envelope",
            "status": precheck_status,
            "executes_runtime_logic": False,
        },
        {
            "step_name": "verify_export_integrity",
            "status": precheck_status,
            "executes_runtime_logic": False,
        },
        {
            "step_name": "validate_manifest_contract",
            "status": precheck_status,
            "executes_runtime_logic": False,
        },
        {
            "step_name": "assess_replay_readiness",
            "status": precheck_status,
            "executes_runtime_logic": False,
        },
        {
            "step_name": "await_explicit_replay_engine_phase",
            "status": "deferred",
            "executes_runtime_logic": False,
        },
    ]

    return {
        "plan_status": "ready" if replay_ready else "blocked",
        "operation_type": "replay_contract_skeleton",
        "replay_execution_enabled": False,
        "replay_contract": replay_contract,
        "replay_steps": replay_steps,
        "summary": {
            "replay_ready": replay_contract["replay_ready"],
            "replay_contract_status": replay_contract["replay_contract_status"],
            "verification_status": replay_contract["verification_status"],
            "blocking_reason_count": len(replay_contract["blocking_reasons"]),
            "warning_count": len(replay_contract["warnings"]),
            "replay_step_count": len(replay_steps),
            "replay_execution_enabled": False,
        },
    }
