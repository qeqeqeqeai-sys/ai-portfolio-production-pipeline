"""Deterministic recovery safety and historical reconstruction closure (Operationalization O2)."""

from __future__ import annotations

from pathlib import Path

from .replay_preflight import build_replay_engine_preflight
from .serialization import stable_checksum

_ALLOWED_STATUSES = {"ready", "blocked", "degraded", "invalid_input"}

_STATUS_EXPLANATIONS = {
    "ready": "Recovery diagnostics and reconstruction metadata are deterministically sufficient for bounded readiness.",
    "blocked": "Recovery diagnostics or reconstruction metadata contain deterministic blocking conditions.",
    "degraded": "Recovery diagnostics or reconstruction metadata are partially sufficient with deterministic degradation conditions.",
    "invalid_input": "Recovery diagnostics cannot be built because the export input is invalid or unreadable.",
}


def _status_rank(status: str) -> int:
    ordering = {"invalid_input": 0, "blocked": 1, "degraded": 2, "ready": 3}
    return ordering.get(status, 0)


def _combine_statuses(*statuses: str) -> str:
    return sorted(statuses, key=_status_rank)[0]


def build_recovery_safety_diagnostics(export_path: str | Path) -> dict:
    """Build deterministic, read-only recovery candidate diagnostics."""

    path = Path(export_path)
    preflight = build_replay_engine_preflight(path)

    verification = preflight.get("verification", {})
    replay_contract = preflight.get("replay_contract", {})

    verification_status = verification.get("verification_status", "invalid")
    contract_status = replay_contract.get("replay_contract_status", "not_replay_ready")
    preflight_status = preflight.get("preflight_status", "failed")

    is_verified = verification.get("is_verified") is True
    contract_ready = replay_contract.get("replay_ready") is True

    diagnostics: list[str] = []
    if not is_verified:
        diagnostics.append("verification_not_verified")
    if not contract_ready:
        diagnostics.append("replay_contract_not_ready")

    warnings = sorted(replay_contract.get("warnings", []))
    blocking_reasons = sorted(replay_contract.get("blocking_reasons", []))

    corruption_signals = sorted([signal for signal in blocking_reasons if "checksum" in signal or "signature" in signal])
    isolation_signals = sorted([signal for signal in blocking_reasons if "isolation" in signal or "boundary" in signal])

    if (not is_verified) or (not contract_ready) or blocking_reasons:
        status = "blocked"
    elif warnings:
        status = "degraded"
    else:
        status = "ready"

    return {
        "status": status,
        "recovery_readiness": status,
        "lineage": {
            "export_path": str(path),
            "export_filename": path.name,
            "verification_status": verification_status,
            "replay_contract_status": contract_status,
            "preflight_status": preflight_status,
            "manifest_checksum": verification.get("observed_manifest_checksum"),
            "signature": verification.get("observed_signature"),
        },
        "candidate_safety_checks": {
            "is_verified": is_verified,
            "replay_contract_ready": contract_ready,
            "preflight_passed": preflight_status == "passed",
            "runtime_replay_disabled": True,
            "artifact_restore_disabled": True,
            "external_mutation_disabled": True,
        },
        "corruption_signals": corruption_signals,
        "isolation_signals": isolation_signals,
        "blocking_reasons": blocking_reasons,
        "warnings": warnings,
        "diagnostics": sorted(set(diagnostics + blocking_reasons + warnings)),
        "allowed_statuses": sorted(_ALLOWED_STATUSES),
        "explanations": {
            "status_explanation": _STATUS_EXPLANATIONS[status],
            "template_version": "deterministic_o2_v1",
        },
    }


def build_historical_reconstruction_summary(export_path: str | Path) -> dict:
    """Build deterministic reconstruction readiness summary from preflight/contract metadata."""

    path = Path(export_path)
    preflight = build_replay_engine_preflight(path)
    verification = preflight.get("verification", {})
    replay_contract = preflight.get("replay_contract", {})

    verification_status = verification.get("verification_status", "invalid")
    contract_status = replay_contract.get("replay_contract_status", "not_replay_ready")
    preflight_status = preflight.get("preflight_status", "failed")

    archive_consistency_checks = {
        "verification_passed": verification.get("is_verified") is True,
    }

    missing_fields = sorted([name for name, ok in archive_consistency_checks.items() if ok is False])
    blocking_reasons = sorted(replay_contract.get("blocking_reasons", []))
    warnings = sorted(replay_contract.get("warnings", []))

    if verification.get("is_verified") is not True:
        status = "blocked"
    elif contract_status != "replay_ready" or warnings or missing_fields:
        status = "degraded"
    else:
        status = "ready"

    return {
        "status": status,
        "reconstruction_readiness": status,
        "lineage": {
            "export_path": str(path),
            "export_filename": path.name,
            "verification_status": verification_status,
            "replay_contract_status": contract_status,
            "preflight_status": preflight_status,
            "manifest_checksum": verification.get("observed_manifest_checksum"),
            "signature": verification.get("observed_signature"),
        },
        "archive_consistency_checks": archive_consistency_checks,
        "missing_fields": missing_fields,
        "blocking_reasons": blocking_reasons,
        "warnings": warnings,
        "diagnostics": sorted(set(missing_fields + blocking_reasons + warnings)),
        "explanations": {
            "status_explanation": _STATUS_EXPLANATIONS[status],
            "template_version": "deterministic_o2_v1",
        },
    }


def run_recovery_historical_closure(export_path: str | Path) -> dict:
    """Run deterministic O2 closure without runtime replay execution or state mutation."""

    path = Path(export_path)
    try:
        recovery_safety = build_recovery_safety_diagnostics(path)
        historical_reconstruction = build_historical_reconstruction_summary(path)
        status = _combine_statuses(recovery_safety.get("status", "invalid_input"), historical_reconstruction.get("status", "invalid_input"))
    except Exception:
        recovery_safety = {
            "status": "invalid_input",
            "diagnostics": ["invalid_export_input"],
            "lineage": {"export_path": str(path), "export_filename": path.name},
        }
        historical_reconstruction = {
            "status": "invalid_input",
            "diagnostics": ["invalid_export_input"],
            "lineage": {"export_path": str(path), "export_filename": path.name},
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
        "closure_phase": "O2_recovery_historical_closure",
        "status": status,
        "recovery_safety": recovery_safety,
        "historical_reconstruction": historical_reconstruction,
        "diagnostics": sorted(set(recovery_safety.get("diagnostics", [])) | set(historical_reconstruction.get("diagnostics", []))),
        "invariants": invariants,
    }
    result["checksum"] = stable_checksum(result, prefix="o2_closure")
    return result
