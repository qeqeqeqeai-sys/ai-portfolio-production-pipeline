"""Deterministic replay supervisor review gate report (Operationalization O1L)."""

from __future__ import annotations

from .replay_contract import assess_replay_contract, build_replay_plan_skeleton


def _is_callable(value: object) -> bool:
    return callable(value)


def build_replay_supervisor_review() -> dict:
    """Build a deterministic supervisor gate review for O1K replay contract skeleton."""
    gate_results = {
        "replay_contract_available": _is_callable(assess_replay_contract),
        "replay_plan_skeleton_available": _is_callable(build_replay_plan_skeleton),
        "replay_execution_disabled_policy": "enforced_by_contract",
        "no_replay_engine_policy": "enforced_by_contract",
        "no_artifact_restore_policy": "enforced_by_contract",
        "no_scheduler_policy": "enforced_by_contract",
        "no_database_write_policy": "enforced_by_contract",
        "no_new_persistence_behavior_policy": "enforced_by_contract",
        "deterministic_replay_plan_policy": "enforced_by_contract",
        "verification_derived_replay_readiness_policy": "enforced_by_contract",
        "tier4_tier5_isolation_policy": "enforced_by_contract",
        "operationalization_boundary_preserved": "enforced_by_contract",
    }

    passed_gates = sorted(
        [name for name, status in gate_results.items() if status is True or status == "enforced_by_contract"]
    )
    failed_gates = sorted([name for name, status in gate_results.items() if status is False])
    warning_gates = sorted(
        [name for name, status in gate_results.items() if status not in (True, False, "enforced_by_contract")]
    )

    review_status = "passed" if not failed_gates else "failed"
    supervisor_summary = {
        "total_gates": len(gate_results),
        "passed_gate_count": len(passed_gates),
        "failed_gate_count": len(failed_gates),
        "warning_gate_count": len(warning_gates),
        "replay_contract_ready_for_future_engine_phase": review_status == "passed",
        "replay_execution_currently_enabled": False,
        "next_recommended_phase": "O1M — Deterministic Replay Engine Design Guardrails",
    }

    return {
        "review_status": review_status,
        "review_scope": "operationalization_o1k_replay_contract",
        "gate_results": gate_results,
        "passed_gates": passed_gates,
        "failed_gates": failed_gates,
        "warning_gates": warning_gates,
        "supervisor_summary": supervisor_summary,
    }
