"""Deterministic replay engine preflight contract report (Operationalization O1N)."""

from __future__ import annotations

from pathlib import Path

from .export_verification import verify_manifest_export_envelope
from .replay_contract import assess_replay_contract
from .replay_guardrails import build_replay_engine_guardrails


def build_replay_engine_preflight(export_path: str | Path) -> dict:
    """Build deterministic preflight checks for a future replay engine contract.

    This function is intentionally read-only and side-effect free beyond reading
    the explicit export path via existing verification/contract helpers.
    """

    path = Path(export_path)
    verification = verify_manifest_export_envelope(path)
    replay_contract = assess_replay_contract(path)
    guardrails = build_replay_engine_guardrails()

    preflight_checks = {
        "export_verification_passed": verification.get("is_verified") is True,
        "replay_contract_ready": replay_contract.get("replay_ready") is True,
        "replay_guardrails_passed": guardrails.get("guardrail_status") == "passed",
        "replay_execution_disabled": True,
        "no_artifact_restore_policy": True,
        "no_scheduler_policy": True,
        "no_database_write_policy": True,
        "no_new_persistence_behavior_policy": True,
        "tier4_tier5_isolation_policy": True,
        "deterministic_report_policy": True,
    }

    failed_checks = sorted([name for name, passed in preflight_checks.items() if passed is False])
    warning_checks: list[str] = []
    passed_checks = sorted(
        [name for name in preflight_checks if name not in failed_checks and name not in warning_checks]
    )

    preflight_status = "passed" if not failed_checks else "failed"

    preflight_summary = {
        "total_checks": len(preflight_checks),
        "passed_check_count": len(passed_checks),
        "failed_check_count": len(failed_checks),
        "warning_check_count": len(warning_checks),
        "replay_engine_allowed_to_execute_now": False,
        "future_engine_phase_required": True,
        "verification_status": verification.get("verification_status", "invalid"),
        "replay_contract_status": replay_contract.get("replay_contract_status", "not_replay_ready"),
        "guardrail_status": guardrails.get("guardrail_status", "failed"),
        "next_recommended_phase": "O1O — Deterministic Replay Engine Dry-Run Executor",
    }

    return {
        "preflight_status": preflight_status,
        "preflight_scope": "future_replay_engine_contract",
        "export_path": str(path),
        "export_filename": path.name,
        "verification": verification,
        "replay_contract": replay_contract,
        "guardrails": guardrails,
        "preflight_checks": preflight_checks,
        "passed_checks": passed_checks,
        "failed_checks": failed_checks,
        "warning_checks": warning_checks,
        "preflight_summary": preflight_summary,
    }
