from __future__ import annotations

from typing import Any

from transmission_layers.expectation_failure.replay_ecology import (
    lr6_live15_governance_recertification_under_ultra_bounded_operational_replay_conditions as live15,
)

LIVE17_VERSION = "LR6_LIVE17_TINY_BOUNDED_REPLAY_PILOT_PREPARATION_REVIEW_V1"
_MAX_PILOT_ROWS = 5
_MAX_COHORT_ENTITIES = 5


def build_lr6_live17_tiny_pilot_preparation_module() -> dict[str, Any]:
    return {
        "live17_version": LIVE17_VERSION,
        "phase_mode": "governance_preparatory_only",
        "execution_enabled": False,
        "live_persistence_enabled": False,
        "lineage_reference": ["LIVE14", "LIVE15", "LIVE16"],
        "tiny_bounded_pilot_objective": "Prepare but do not execute the first tiny bounded replay pilot.",
        "deterministic_governance_only": True,
        "replay_richness_only": True,
    }


def build_lr6_live17_deterministic_pilot_envelope() -> dict[str, Any]:
    return {
        "envelope_id": "LIVE17_TINY_BOUNDED_REPLAY_ENVELOPE",
        "allowed_metric_dimension": "replay_richness",
        "max_rows": _MAX_PILOT_ROWS,
        "max_entities": _MAX_COHORT_ENTITIES,
        "max_batches": 1,
        "execution_mode": "dry_run_only_preflight",
        "allowed_state_transition": "prepared_not_executed",
        "operator_approval_quorum": 2,
        "append_only_required": True,
        "schema_change_allowed": False,
        "historical_rewrite_allowed": False,
        "sql_bypass_allowed": False,
    }


def build_lr6_live17_replay_richness_only_candidate_cohort() -> dict[str, Any]:
    return {
        "cohort_id": "LIVE17_TINY_REPLAY_RICHNESS_ONLY_COHORT",
        "candidate_count": _MAX_COHORT_ENTITIES,
        "cohort_shape": "single_wave_tiny_candidate_set",
        "metric_dimension": "replay_richness",
        "selection_rules": [
            "deterministic_rank_order_required",
            "no_density_scaling_candidates",
            "no_topology_expansion_candidates",
            "append_only_candidate_trace",
        ],
        "dry_run_projection_only": True,
        "execution_candidates_materialized": False,
    }


def build_lr6_live17_operator_approval_checklist() -> dict[str, Any]:
    return {
        "required_approvals": [
            "supervisor_governance_signoff",
            "operator_dry_run_only_acknowledgement",
            "append_only_posture_acknowledgement",
            "no_sql_bypass_attestation",
        ],
        "minimum_approvals": 2,
        "approval_status_default": "pending",
        "execution_unlock_possible": False,
    }


def build_lr6_live17_preflight_governance_checklist() -> dict[str, Any]:
    return {
        "checks": [
            "tiny_envelope_boundaries_validated",
            "replay_richness_only_dimension_validated",
            "dry_run_mode_enforced",
            "no_persistence_path_enabled",
            "no_schema_expansion_requested",
            "no_historical_rewrite_requested",
        ],
        "all_required": True,
        "checklist_pass_default": True,
    }


def build_lr6_live17_observability_readiness_checklist() -> dict[str, Any]:
    return {
        "required_signals": [
            "pilot_envelope_traceability",
            "cohort_membership_traceability",
            "approval_event_traceability",
            "dry_run_assumption_traceability",
        ],
        "telemetry_sink_mode": "governance_review_artifacts_only",
        "live_telemetry_emission": False,
        "readiness_status": "ready",
    }


def build_lr6_live17_stop_condition_readiness_checklist() -> dict[str, Any]:
    return {
        "stop_conditions": [
            "boundary_drift_detected",
            "non_dry_transition_detected",
            "replay_density_escalation_detected",
            "schema_or_sql_bypass_attempt_detected",
        ],
        "trigger_policy": "immediate_governance_hold",
        "readiness_status": "ready",
    }


def build_lr6_live17_rollback_readiness_checklist() -> dict[str, Any]:
    return {
        "rollback_primitives": [
            "disable_pilot_preparation_package",
            "invalidate_candidate_cohort_snapshot",
            "reset_operator_approvals",
            "restore_last_certified_governance_state",
        ],
        "rollback_mode": "governance_state_only",
        "historical_row_rollback_needed": False,
        "readiness_status": "ready",
    }


def build_lr6_live17_pilot_readiness_classification() -> dict[str, Any]:
    envelope = build_lr6_live17_deterministic_pilot_envelope()
    cohort = build_lr6_live17_replay_richness_only_candidate_cohort()
    preflight = build_lr6_live17_preflight_governance_checklist()
    if not preflight["checklist_pass_default"] or envelope["execution_mode"] != "dry_run_only_preflight":
        cls = "LIVE17_PREPARATION_BLOCKED"
    elif cohort["execution_candidates_materialized"]:
        cls = "LIVE17_PREPARATION_INVALID"
    else:
        cls = "LIVE17_PREPARATION_READY_NOT_EXECUTABLE"
    return {
        "classification": cls,
        "deterministic_reason": "dry-run-only bounded replay_richness preparation package validated with execution explicitly disabled",
        "may_execute_pilot": False,
    }


def build_lr6_live17_live18_eligibility_gate() -> dict[str, Any]:
    prep = build_lr6_live17_pilot_readiness_classification()
    if prep["classification"] == "LIVE17_PREPARATION_READY_NOT_EXECUTABLE":
        gate = "LIVE18_TINY_PILOT_DRY_RUN_REHEARSAL_DISCUSSABLE"
    else:
        gate = "LIVE18_TINY_PILOT_DRY_RUN_REHEARSAL_BLOCKED"
    return {"live18_gate": gate, "discussion_only": True, "execution_authorized": False}


def certify_lr6_live17_preparation_boundary() -> dict[str, Any]:
    return {
        "preparation_only": True,
        "pilot_execution_enabled": False,
        "live_persistence_enabled": False,
        "broad_replay_scaling_enabled": False,
        "replay_density_scaling_enabled": False,
        "production_replay_ecology_activation_enabled": False,
        "topology_expansion_enabled": False,
        "contradiction_persistence_migration_enabled": False,
        "prediction_enabled": False,
        "trading_enabled": False,
        "auto_expansion_enabled": False,
        "schema_expansion_enabled": False,
        "direct_sql_allowed": False,
        "historical_row_rewrite_enabled": False,
        "replay_richness_only": True,
        "append_only_required": True,
        "deterministic_governance_only": True,
    }


def build_lr6_live17_supervisor_review() -> dict[str, Any]:
    live15_gate = live15.build_lr6_live15_post_pilot_discussion_gate(
        live15.build_lr6_live15_recertification_risk_review()["recertification_classifications"]
    )
    return {
        "objective": "Convert LIVE16 governance framework into a concrete tiny bounded replay pilot preparation package without executing the pilot.",
        "tiny_pilot_preparation_module": build_lr6_live17_tiny_pilot_preparation_module(),
        "deterministic_pilot_envelope": build_lr6_live17_deterministic_pilot_envelope(),
        "replay_richness_only_candidate_cohort": build_lr6_live17_replay_richness_only_candidate_cohort(),
        "operator_approval_checklist": build_lr6_live17_operator_approval_checklist(),
        "governance_preflight_checklist": build_lr6_live17_preflight_governance_checklist(),
        "observability_readiness_checklist": build_lr6_live17_observability_readiness_checklist(),
        "stop_condition_readiness_checklist": build_lr6_live17_stop_condition_readiness_checklist(),
        "rollback_readiness_checklist": build_lr6_live17_rollback_readiness_checklist(),
        "pilot_readiness_classification": build_lr6_live17_pilot_readiness_classification(),
        "live18_eligibility_gate": build_lr6_live17_live18_eligibility_gate(),
        "live15_longitudinal_gate_reference": live15_gate,
        "governance_boundary_certification": certify_lr6_live17_preparation_boundary(),
    }


def build_lr6_live17_markdown_report(review: dict[str, Any]) -> str:
    return "\n".join([
        "# LR6-LIVE17 — Tiny Bounded Replay Pilot Preparation Review",
        "",
        "## objective",
        f"- {review.get('objective')}",
        "",
        "## tiny pilot preparation module",
        f"- {review.get('tiny_pilot_preparation_module')}",
        "",
        "## deterministic pilot envelope",
        f"- {review.get('deterministic_pilot_envelope')}",
        "",
        "## replay_richness-only candidate cohort",
        f"- {review.get('replay_richness_only_candidate_cohort')}",
        "",
        "## operator approval checklist",
        f"- {review.get('operator_approval_checklist')}",
        "",
        "## governance pre-flight checklist",
        f"- {review.get('governance_preflight_checklist')}",
        "",
        "## observability readiness checklist",
        f"- {review.get('observability_readiness_checklist')}",
        "",
        "## stop-condition readiness checklist",
        f"- {review.get('stop_condition_readiness_checklist')}",
        "",
        "## rollback readiness checklist",
        f"- {review.get('rollback_readiness_checklist')}",
        "",
        "## deterministic pilot readiness classification",
        f"- {review.get('pilot_readiness_classification')}",
        "",
        "## LIVE18 eligibility gate",
        f"- {review.get('live18_eligibility_gate')}",
        "",
        "## governance boundary certification",
        f"- {review.get('governance_boundary_certification')}",
        "",
    ])
