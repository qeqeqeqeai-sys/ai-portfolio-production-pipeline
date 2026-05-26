"""LR6-EXEC1 first governed bounded enriched replay observation wave (dry-governed, fail-closed)."""
from __future__ import annotations

from typing import Any

from transmission_layers.expectation_failure.replay_ecology.lr6_obs6_first_enriched_replay_wave_design import (
    TARGET_WAVE_SIZE,
    build_lr6_obs6_first_wave_candidates,
)
from transmission_layers.expectation_failure.replay_ecology.lr6_obs9_execution_review_framework import (
    build_lr6_obs9_failure_criteria,
)

DETERMINISTIC_VERSION = "LR6_EXEC1_FIRST_GOVERNED_BOUNDED_ENRICHED_REPLAY_WAVE_V1"
SOURCE_PHASE = "LR6-EXEC1"

REQUIRED_APPROVALS = {
    "operator_approval_phrase": "APPROVED_LR6_EXEC1_NON_DRY_OBSERVATION",
    "ack_non_dry_observation": "ACK_NON_DRY_REPLAY_OBSERVATION",
    "ack_bounded_first_wave_scope": "ACK_BOUNDED_FIRST_WAVE_SCOPE_16",
    "ack_stop_after_first_wave": "ACK_STOP_AFTER_FIRST_WAVE",
    "ack_review_before_continuation": "ACK_REVIEW_BEFORE_CONTINUATION",
    "ack_observation_only": "ACK_OBSERVATION_ONLY_NO_EXECUTION_ALPHA",
    "ack_no_prediction_or_trading": "ACK_NO_PREDICTION_OR_TRADING_AUTHORIZATION",
}


def build_lr6_exec1_execution_context() -> dict[str, Any]:
    return {
        "deterministic_version": DETERMINISTIC_VERSION,
        "source_phase": SOURCE_PHASE,
        "execution_mode": "dry_governed_fail_closed",
        "default_mode": "DRY_RUN_ONLY",
        "bounded_wave_size": TARGET_WAVE_SIZE,
        "stop_after_first_wave_required": True,
        "append_only_governance_required": True,
        "observation_only": True,
        "no_prediction": True,
        "no_trading": True,
        "no_direct_sql": True,
    }


def build_lr6_exec1_wave_preparation() -> dict[str, Any]:
    selected = build_lr6_obs6_first_wave_candidates(TARGET_WAVE_SIZE)
    return {
        "selected_count": len(selected),
        "target_count": TARGET_WAVE_SIZE,
        "selected_candidates": selected,
        "bounded_selection_enforced": len(selected) == TARGET_WAVE_SIZE,
        "stop_after_first_wave": True,
    }


def validate_lr6_exec1_governance_approvals(approvals: dict[str, Any] | None = None) -> dict[str, Any]:
    provided = approvals if isinstance(approvals, dict) else {}
    checks = []
    missing = []
    malformed = []
    for key, expected in REQUIRED_APPROVALS.items():
        actual = str(provided.get(key, "")).strip()
        ok = actual == expected
        checks.append({"key": key, "expected": expected, "actual": actual, "approved": ok})
        if actual == "":
            missing.append(key)
        elif not ok:
            malformed.append(key)

    approved = not missing and not malformed
    return {
        "required": REQUIRED_APPROVALS.copy(),
        "checks": checks,
        "approved": approved,
        "fail_closed": not approved,
        "blocking_reasons": [
            *(["missing_required_approvals"] if missing else []),
            *(["malformed_required_approvals"] if malformed else []),
        ],
        "missing": missing,
        "malformed": malformed,
    }


def build_lr6_exec1_expected_artifacts() -> list[dict[str, str]]:
    artifacts = [
        "enriched_replay_observation_review",
        "contradiction_migration_review",
        "propagation_topology_delta_review",
        "weak_signal_attribution_review",
        "replay_saturation_review",
        "governance_execution_review",
        "stop_condition_evaluation_review",
        "continuation_recommendation_review",
    ]
    return [{"artifact": name, "deterministic": "true"} for name in artifacts]


def _build_fail_closed_evaluation_stub() -> dict[str, Any]:
    return {
        "status": "FAIL_CLOSED_UNTIL_SUPERVISOR_REVIEW",
        "failure_criteria": build_lr6_obs9_failure_criteria(),
        "triggered": ["review_not_executed_yet"],
        "continuation_allowed": False,
    }


def execute_lr6_exec1_first_wave(*, approvals: dict[str, Any] | None = None, dry_run: bool = True) -> dict[str, Any]:
    governance = validate_lr6_exec1_governance_approvals(approvals)
    prep = build_lr6_exec1_wave_preparation()
    mode = "DRY_RUN" if dry_run else "NON_DRY_REQUESTED"

    if dry_run:
        status = "DRY_RUN_COMPLETED"
        executed_non_dry = False
        block_reasons: list[str] = []
    elif not governance["approved"]:
        status = "GOVERNANCE_BLOCKED_FAIL_CLOSED"
        executed_non_dry = False
        block_reasons = ["non_dry_requires_full_explicit_approvals", *governance["blocking_reasons"]]
    else:
        status = "NON_DRY_APPROVED_BUT_STOPPED_AFTER_FIRST_WAVE"
        executed_non_dry = True
        block_reasons = ["automatic_continuation_prohibited", "supervisor_review_required_before_any_continuation"]

    return {
        "context": build_lr6_exec1_execution_context(),
        "wave_preparation": prep,
        "governance_approval_validation": governance,
        "execution": {
            "requested_mode": mode,
            "dry_run": bool(dry_run),
            "status": status,
            "executed_non_dry": executed_non_dry,
            "no_write_path_performed": True,
            "stop_after_first_wave_enforced": True,
            "automatic_continuation_allowed": False,
            "recursive_expansion_allowed": False,
            "blocking_reasons": block_reasons,
        },
        "execution_review_artifacts": build_lr6_exec1_expected_artifacts(),
        "fail_closed_review": _build_fail_closed_evaluation_stub(),
        "execution_boundary_certification": {
            "observation_only": True,
            "dry_run_default": True,
            "governance_gated_non_dry": True,
            "fail_closed_enforced": True,
            "stop_after_first_wave_enforced": True,
            "review_before_continuation_required": True,
            "no_prediction": True,
            "no_trading": True,
            "no_direct_sql": True,
            "no_recursive_execution": True,
            "append_only_governance_discipline_preserved": True,
        },
    }
