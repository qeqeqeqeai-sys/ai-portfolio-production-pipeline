"""LR6-EXEC2 first dry-run execution review for bounded enriched replay observation."""
from __future__ import annotations

from collections import Counter
from typing import Any

from transmission_layers.expectation_failure.replay_ecology.lr6_exec1_first_governed_bounded_enriched_replay_wave import (
    execute_lr6_exec1_first_wave,
)
from transmission_layers.expectation_failure.replay_ecology.lr6_evid6_minimal_in_memory_metrics_emission_hook import (
    emit_lr6_replay_metric_evidence,
)

DETERMINISTIC_VERSION = "LR6_EXEC2_FIRST_DRY_RUN_EXECUTION_REVIEW_V1"
SOURCE_PHASE = "LR6-EXEC2"


def _role_counts(candidates: list[dict[str, Any]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for c in candidates:
        roles = c.get("roles")
        if isinstance(roles, list) and roles:
            for role in roles:
                counter[str(role)] += 1
        else:
            counter["unknown"] += 1
    return dict(sorted(counter.items()))




def _build_dry_run_replay_metric_payload(dry_artifact: dict[str, Any]) -> dict[str, Any]:
    execution = dry_artifact.get("execution", {}) if isinstance(dry_artifact, dict) else {}
    return {
        "dry_run": execution.get("dry_run") is True,
        "execution_authorized": execution.get("executed_non_dry") is True,
        "governance_review": {"status": execution.get("status", "DRY_RUN_COMPLETED")},
        "review_sections": [a.get("artifact") for a in dry_artifact.get("execution_review_artifacts", []) if isinstance(a, dict)],
        "stop_after_first_wave": execution.get("stop_after_first_wave_enforced") is True,
    }


def _build_evidence_emission_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "evidence_record_count": len(records),
        "measured_record_count": sum(1 for r in records if r.get("evidence_status") == "MEASURED"),
        "partial_record_count": sum(1 for r in records if r.get("evidence_status") == "PARTIAL"),
        "missing_record_count": sum(1 for r in records if r.get("evidence_status") == "MISSING"),
        "scaffold_only_record_count": sum(1 for r in records if r.get("evidence_status") == "SCAFFOLD_ONLY"),
        "comparison_ready_record_count": sum(1 for r in records if r.get("comparison_ready") is True),
        "evidence_hook_source": "lr6_evid6_minimal_in_memory_metrics_emission_hook.emit_lr6_replay_metric_evidence",
    }

def build_lr6_exec2_first_dry_run_execution_review() -> dict[str, Any]:
    dry = execute_lr6_exec1_first_wave(dry_run=True, approvals=None)

    candidates = list(dry.get("wave_preparation", {}).get("selected_candidates", []))
    selected_count = int(dry.get("wave_preparation", {}).get("selected_count", 0))
    role_balance = _role_counts(candidates)
    known_role_candidates = sum(1 for c in candidates if isinstance(c.get("roles"), list) and len(c.get("roles", [])) > 0)
    unknown_role_candidates = selected_count - known_role_candidates
    weak_signal_count = sum(1 for c in candidates if c.get("weak_signal_bridge") is True)
    contradiction_count = sum(1 for c in candidates if c.get("contradiction_carrier") is True)
    propagation_count = sum(1 for c in candidates if c.get("propagation_bridge") is True)

    execution = dry.get("execution", {})
    boundary = dry.get("execution_boundary_certification", {})
    governance = dry.get("governance_approval_validation", {})

    replay_metric_payload = _build_dry_run_replay_metric_payload(dry)
    evidence_records = emit_lr6_replay_metric_evidence(
        replay_phase="ENRICHED",
        wave_id="LR6_EXEC2_DRY_RUN_WAVE1",
        candidate_scope_id="LR6_EXEC2_DRY_RUN_SCOPE_16",
        candidate_count=selected_count,
        timestamp_or_snapshot_label="LR6_EXEC2_DRY_RUN",
        replay_observation_payload=replay_metric_payload,
        candidate_metadata=candidates,
        source_artifact="lr6_exec2_first_dry_run_execution_review",
        source_module=SOURCE_PHASE,
    )
    evidence_summary = _build_evidence_emission_summary(evidence_records)

    return {
        "meta": {
            "deterministic_version": DETERMINISTIC_VERSION,
            "source_phase": SOURCE_PHASE,
            "review_scope": "dry_run_only_first_wave",
        },
        "dry_run_execution_review": {
            "dry_run_path_executed": execution.get("dry_run") is True,
            "status": execution.get("status"),
            "deterministic_posture": dry == execute_lr6_exec1_first_wave(dry_run=True, approvals=None),
            "non_dry_activation_detected": execution.get("executed_non_dry") is True,
        },
        "wave_assembly_review": {
            "candidate_count": selected_count,
            "expected_count": 16,
            "count_match": selected_count == 16,
            "role_balance": role_balance,
            "required_roles_present": {
                "weak_signal": weak_signal_count > 0,
                "contradiction": contradiction_count > 0,
                "propagation": propagation_count > 0,
            },
            "role_attribution": {
                "total_candidates": selected_count,
                "known_role_metadata_count": known_role_candidates,
                "unknown_role_metadata_count": unknown_role_candidates,
                "weak_signal_count": weak_signal_count,
                "contradiction_carrier_count": contradiction_count,
                "propagation_bridge_count": propagation_count,
                "role_metadata_preserved": known_role_candidates > 0,
                "any_missing_role_metadata": unknown_role_candidates > 0,
            },
        },
        "governance_behavior_review": {
            "dry_run_default": boundary.get("dry_run_default") is True,
            "governance_gating_enabled": boundary.get("governance_gated_non_dry") is True,
            "fail_closed_enforced": boundary.get("fail_closed_enforced") is True,
            "approval_model": {
                "approved": governance.get("approved"),
                "fail_closed": governance.get("fail_closed"),
            },
        },
        "fail_closed_behavior_review": {
            "no_persistence_writes": execution.get("no_write_path_performed") is True,
            "non_dry_blocked_without_approvals": governance.get("approved") is False,
            "fail_closed_status": dry.get("fail_closed_review", {}).get("status"),
        },
        "execution_artifact_review": {
            "artifact_count": len(dry.get("execution_review_artifacts", [])),
            "artifacts_present": [a.get("artifact") for a in dry.get("execution_review_artifacts", [])],
            "operationally_usable": len(dry.get("execution_review_artifacts", [])) >= 6,
            "genericity_risk": "medium",
            "notes": "Artifacts are structurally complete but still template-like and should be populated with observed evidence in non-dry governed execution.",
        },
        "stop_after_first_wave_review": {
            "stop_after_first_wave_enforced": execution.get("stop_after_first_wave_enforced") is True,
            "automatic_continuation_prevented": execution.get("automatic_continuation_allowed") is False,
            "recursive_expansion_absent": execution.get("recursive_expansion_allowed") is False,
        },
        "operational_usability_assessment": {
            "bounded_and_reviewable": True,
            "ambiguities": [
                "Role labels rely on source candidate schema; explicit contract test should remain mandatory.",
                "Artifact payloads are scaffold-level and need stricter evidence fields before non-dry review depth claims.",
            ],
            "governance_excess_risk": "low_to_medium",
        },
        "overengineering_assessment": {
            "direction": "approaching_useful_ecological_experimentation",
            "anti_hype_guardrail": "dry-run output validates controls, not ecological intelligence gains",
            "complexity_judgment": "currently_justified_if_non_dry_scope_remains_single_wave_and_review_first",
        },
        "validation_checks": {
            "dry_run_true": execution.get("dry_run") is True,
            "execution_authorized_false": execution.get("executed_non_dry") is False,
            "no_persistence_writes": execution.get("no_write_path_performed") is True,
            "governance_gating_intact": boundary.get("governance_gated_non_dry") is True,
            "stop_after_first_wave_true": execution.get("stop_after_first_wave_enforced") is True,
            "no_recursive_continuation": execution.get("recursive_expansion_allowed") is False,
            "no_direct_sql_boundary": boundary.get("no_direct_sql") is True,
            "outputs_bounded_reviewable": len(dry.get("execution_review_artifacts", [])) == 8,
        },
        "evidence_emission_mode": "DRY_RUN_IN_MEMORY",
        "evidence_records_are_empirical": False,
        "evidence_records": evidence_records,
        "evidence_emission_summary": evidence_summary,
        "recommendation": {
            "decision": "proceed_to_one_bounded_governed_non_dry_observation_wave",
            "conditions": [
                "Keep single-wave stop condition hard-enforced.",
                "Require full explicit approvals exactly as defined in EXEC1.",
                "Capture evidence-rich artifact content and run immediate supervisor review before any continuation request.",
            ],
        },
    }


__all__ = ["build_lr6_exec2_first_dry_run_execution_review"]
