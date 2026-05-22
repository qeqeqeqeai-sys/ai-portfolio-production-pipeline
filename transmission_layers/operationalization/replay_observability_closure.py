"""Deterministic replay integrity and observability closure (Operationalization O1P)."""

from __future__ import annotations

from pathlib import Path

from .replay_dry_run import execute_replay_dry_run
from .serialization import stable_checksum

_ALLOWED_STATUSES = {"ready", "blocked", "degraded", "invalid_input"}


_DEF_EXPLANATIONS = {
    "ready": "Replay dry-run and preflight checks are structurally ready with deterministic safeguards in place.",
    "blocked": "Replay closure is blocked by verification or contract-level failures and cannot progress.",
    "degraded": "Replay closure is degraded due to warnings or deferred-only progress despite deterministic safety invariants.",
    "invalid_input": "Replay closure input is invalid or unreadable for deterministic assessment.",
}


def _status_from_dry_run(dry_run: dict) -> str:
    execution_status = dry_run.get("execution_status")
    plan_status = dry_run.get("replay_plan", {}).get("plan_status")
    warning_count = len(dry_run.get("preflight", {}).get("warning_checks", []))

    if execution_status == "blocked" or plan_status == "blocked":
        return "blocked"
    if warning_count > 0:
        return "degraded"
    return "ready"


def build_replay_integrity_diagnostics(export_path: str | Path) -> dict:
    """Build deterministic replay integrity diagnostics for dry-run output stability."""

    path = Path(export_path)
    first = execute_replay_dry_run(path)
    second = execute_replay_dry_run(path)

    first_projection_checksum = stable_checksum(first.get("replay_plan", {}), prefix="o1p_plan")
    second_projection_checksum = stable_checksum(second.get("replay_plan", {}), prefix="o1p_plan")
    full_dry_run_checksum = stable_checksum(first, prefix="o1p_dryrun")

    deterministic_repeated_output = first == second
    checksum_stable = first_projection_checksum == second_projection_checksum

    status = _status_from_dry_run(first)
    if deterministic_repeated_output is False or checksum_stable is False:
        status = "degraded"

    diagnostics = []
    if deterministic_repeated_output is False:
        diagnostics.append("repeated_output_mismatch")
    if checksum_stable is False:
        diagnostics.append("replay_plan_checksum_mismatch")

    return {
        "status": status,
        "replay_plan_status": first.get("replay_plan", {}).get("plan_status"),
        "dry_run_execution_status": first.get("execution_status"),
        "deterministic_repeated_output": deterministic_repeated_output,
        "replay_plan_checksum": first_projection_checksum,
        "replay_plan_checksum_stable": checksum_stable,
        "dry_run_projection_checksum": full_dry_run_checksum,
        "diagnostics": diagnostics,
        "readiness_category": status,
        "allowed_statuses": sorted(_ALLOWED_STATUSES),
    }


def build_replay_observability_summary(export_path: str | Path) -> dict:
    """Build deterministic structural observability summary for replay transmission state."""

    path = Path(export_path)
    dry_run = execute_replay_dry_run(path)
    summary = dry_run.get("execution_summary", {})
    replay_contract = dry_run.get("replay_plan", {}).get("replay_contract", {})

    status = _status_from_dry_run(dry_run)

    degraded_reasons = sorted(replay_contract.get("warnings", []))
    blocked_reasons = sorted(replay_contract.get("blocking_reasons", []))
    degradation_state = "none"
    if status == "degraded":
        degradation_state = "degraded"
    if status == "blocked":
        degradation_state = "blocked"

    lineage = {
        "export_path": dry_run.get("export_path"),
        "export_filename": dry_run.get("export_filename"),
        "verification_status": replay_contract.get("verification_status"),
        "replay_contract_status": replay_contract.get("replay_contract_status"),
        "preflight_status": dry_run.get("preflight", {}).get("preflight_status"),
    }

    return {
        "status": status,
        "degradation_state": degradation_state,
        "lineage": lineage,
        "counts": {
            "total_replay_steps": summary.get("total_replay_steps", 0),
            "executed_step_count": summary.get("executed_step_count", 0),
            "deferred_step_count": summary.get("deferred_step_count", 0),
            "blocked_step_count": summary.get("blocked_step_count", 0),
            "blocking_reason_count": len(blocked_reasons),
            "warning_count": len(degraded_reasons),
        },
        "blocked_reasons": blocked_reasons,
        "degraded_reasons": degraded_reasons,
        "explanations": {
            "status_explanation": _DEF_EXPLANATIONS[status],
            "degradation_explanation": (
                "No degradation detected." if degradation_state == "none" else f"Deterministic {degradation_state} conditions detected."
            ),
        },
    }


def run_replay_observability_closure(export_path: str | Path) -> dict:
    """Run O1 replay/observability closure without runtime replay execution or mutation."""

    path = Path(export_path)
    try:
        replay_integrity = build_replay_integrity_diagnostics(path)
        observability = build_replay_observability_summary(path)
        status = replay_integrity.get("status", "invalid_input")
        if status not in _ALLOWED_STATUSES:
            status = "invalid_input"
    except Exception:
        replay_integrity = {
            "status": "invalid_input",
            "diagnostics": ["invalid_export_input"],
            "allowed_statuses": sorted(_ALLOWED_STATUSES),
        }
        observability = {
            "status": "invalid_input",
            "degradation_state": "blocked",
            "lineage": {"export_path": str(path), "export_filename": path.name},
            "counts": {
                "total_replay_steps": 0,
                "executed_step_count": 0,
                "deferred_step_count": 0,
                "blocked_step_count": 0,
                "blocking_reason_count": 0,
                "warning_count": 0,
            },
            "blocked_reasons": ["invalid_export_input"],
            "degraded_reasons": [],
            "explanations": {
                "status_explanation": _DEF_EXPLANATIONS["invalid_input"],
                "degradation_explanation": "Deterministic blocked conditions detected.",
            },
        }
        status = "invalid_input"

    invariants = {
        "executes_runtime_logic": False,
        "restores_artifacts": False,
        "mutates_external_state": False,
        "uses_prediction": False,
        "uses_optimization": False,
        "uses_adaptive_control": False,
    }

    result = {
        "closure_phase": "O1_replay_observability_closure",
        "status": status,
        "replay_integrity": replay_integrity,
        "observability": observability,
        "diagnostics": sorted(
            set(replay_integrity.get("diagnostics", []))
            | set(observability.get("blocked_reasons", []))
            | set(observability.get("degraded_reasons", []))
        ),
        "invariants": invariants,
    }
    result["checksum"] = stable_checksum(result, prefix="o1p_closure")
    return result
