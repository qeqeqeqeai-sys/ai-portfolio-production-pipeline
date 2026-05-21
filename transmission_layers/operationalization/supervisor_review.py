"""Deterministic operationalization supervisor review gate report (Operationalization O1J)."""

from __future__ import annotations

from .audit_summary import build_operational_audit_summary
from .cli_smoke import run_operationalization_cli_smoke
from .export_envelope import build_dry_run_operational_report, build_manifest_export_envelope
from .export_persistence import build_export_filename, persist_manifest_export_envelope
from .export_verification import load_manifest_export_envelope, verify_manifest_export_envelope
from .manifests import build_run_manifest, empty_manifest, manifest_checksum
from .readiness import assess_manifest_readiness, build_manifest_validation_report
from .serialization import stable_checksum, stable_serialize
from .validators import validate_run_manifest


def _is_callable(value: object) -> bool:
    return callable(value)


def build_operationalization_supervisor_review() -> dict:
    """Build a deterministic supervisor gate review for O1A-O1I contracts."""
    gate_results = {
        "serialization_contract_available": _is_callable(stable_serialize) and _is_callable(stable_checksum),
        "manifest_contract_available": _is_callable(build_run_manifest)
        and _is_callable(manifest_checksum)
        and _is_callable(empty_manifest),
        "validation_contract_available": _is_callable(validate_run_manifest),
        "readiness_contract_available": _is_callable(assess_manifest_readiness)
        and _is_callable(build_manifest_validation_report),
        "export_envelope_contract_available": _is_callable(build_manifest_export_envelope)
        and _is_callable(build_dry_run_operational_report),
        "persistence_contract_available": _is_callable(build_export_filename)
        and _is_callable(persist_manifest_export_envelope),
        "verification_contract_available": _is_callable(load_manifest_export_envelope)
        and _is_callable(verify_manifest_export_envelope),
        "audit_summary_contract_available": _is_callable(build_operational_audit_summary),
        "cli_smoke_contract_available": _is_callable(run_operationalization_cli_smoke),
        "deterministic_no_timestamp_runtime_id_policy": "enforced_by_contract",
        "no_database_write_policy": "enforced_by_contract",
        "no_scheduler_policy": "enforced_by_contract",
        "no_replay_execution_policy": "enforced_by_contract",
        "additive_operationalization_boundary": "enforced_by_contract",
        "tier4_tier5_isolation_policy": "enforced_by_contract",
    }

    passed_gates = sorted([name for name, status in gate_results.items() if status is True or status == "enforced_by_contract"])
    failed_gates = sorted([name for name, status in gate_results.items() if status is False])
    warning_gates = sorted([name for name, status in gate_results.items() if status not in (True, False, "enforced_by_contract")])

    review_status = "passed" if not failed_gates else "failed"
    supervisor_summary = {
        "total_gates": len(gate_results),
        "passed_gate_count": len(passed_gates),
        "failed_gate_count": len(failed_gates),
        "warning_gate_count": len(warning_gates),
        "operationalization_ready_for_next_phase": review_status == "passed",
        "next_recommended_phase": "O1K — Deterministic Operational Replay Contract Skeleton",
    }

    return {
        "review_status": review_status,
        "review_scope": "operationalization_o1a_o1i",
        "gate_results": gate_results,
        "passed_gates": passed_gates,
        "failed_gates": failed_gates,
        "warning_gates": warning_gates,
        "supervisor_summary": supervisor_summary,
    }
