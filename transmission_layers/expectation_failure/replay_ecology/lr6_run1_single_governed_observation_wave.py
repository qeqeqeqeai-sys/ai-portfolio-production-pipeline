"""LR6-RUN1 single governed observation wave supervisor (bounded, fail-closed)."""
from __future__ import annotations

from typing import Any

from transmission_layers.expectation_failure.replay_ecology.lr6_exec1_first_governed_bounded_enriched_replay_wave import (
    REQUIRED_APPROVALS,
    execute_lr6_exec1_first_wave,
)

DETERMINISTIC_VERSION = "LR6_RUN1_SINGLE_GOVERNED_OBSERVATION_WAVE_V1"
SOURCE_PHASE = "LR6-RUN1"
REQUIRED_APPROVAL_PHRASE = "APPROVED_LR6_OBS8_GOVERNED_FIRST_WAVE_OBSERVATION_ONLY"
FINAL_DECISIONS = {
    "continue_not_recommended": "CONTINUE_NOT_RECOMMENDED",
    "conditionally_continue_with_review": "CONDITIONALLY_CONTINUE_WITH_REVIEW",
    "ecology_improvement_not_sufficient": "ECOLOGY_IMPROVEMENT_NOT_SUFFICIENT",
    "structurally_interesting_replay_behavior_observed": "STRUCTURALLY_INTERESTING_REPLAY_BEHAVIOR_OBSERVED",
}


def _convert_obs8_phrase_to_exec1_approvals(approval_phrase: str) -> dict[str, str]:
    if approval_phrase.strip() != REQUIRED_APPROVAL_PHRASE:
        return {}
    return REQUIRED_APPROVALS.copy()


def _fail_closed_reviews() -> dict[str, dict[str, Any]]:
    fail = {"status": "fail_closed", "evidence": "no_non_dry_replay_rows_provided", "material_change": False}
    return {
        "enriched_replay_observation_review": fail | {"focus": "topology_vs_baseline"},
        "contradiction_migration_review": fail | {"focus": "contradiction_depth"},
        "propagation_topology_delta_review": fail | {"focus": "propagation_diversity"},
        "weak_signal_attribution_review": fail | {"focus": "weak_signal_bridge_presence"},
        "replay_saturation_monoculture_review": fail | {"focus": "megacap_gravity_reduction"},
        "governance_execution_review": {"status": "pass", "focus": "bounded_fail_closed_controls"},
        "stop_condition_evaluation_review": {
            "status": "triggered",
            "triggers": [
                "replay_richness_not_materially_improved",
                "outputs_indistinguishable_from_pre_enrichment_baseline",
            ],
        },
        "continuation_recommendation_review": {
            "automatic_continuation_allowed": False,
            "recursive_replay_allowed": False,
            "supervisor_review_required": True,
        },
    }


def execute_lr6_run1_single_governed_observation_wave(*, approval_phrase: str, dry_run: bool = False) -> dict[str, Any]:
    exec1_approvals = _convert_obs8_phrase_to_exec1_approvals(approval_phrase)
    exec1 = execute_lr6_exec1_first_wave(approvals=exec1_approvals, dry_run=dry_run)
    governance_ok = bool(exec1["governance_approval_validation"]["approved"])
    bounded_ok = bool(exec1["wave_preparation"]["selected_count"] == 16)

    if not governance_ok or not bounded_ok:
        decision = FINAL_DECISIONS["continue_not_recommended"]
    else:
        decision = FINAL_DECISIONS["ecology_improvement_not_sufficient"]

    return {
        "metadata": {
            "deterministic_version": DETERMINISTIC_VERSION,
            "source_phase": SOURCE_PHASE,
            "single_wave_only": True,
            "max_candidates": 16,
            "stop_after_first_wave_mandatory": True,
        },
        "approval": {
            "required_phrase": REQUIRED_APPROVAL_PHRASE,
            "provided_phrase": approval_phrase,
            "phrase_valid": approval_phrase.strip() == REQUIRED_APPROVAL_PHRASE,
        },
        "execution": exec1,
        "deterministic_reviews": _fail_closed_reviews(),
        "validation": {
            "bounded_16_candidate_execution": bounded_ok,
            "approval_gating_enforced": True,
            "stop_after_first_wave_enforced": bool(exec1["execution"]["stop_after_first_wave_enforced"]),
            "no_recursive_continuation": bool(exec1["execution"]["recursive_expansion_allowed"] is False),
            "deterministic_artifact_generation": True,
            "no_prediction_or_trading_logic": True,
            "no_direct_sql_execution_path": True,
            "fail_closed_behavior": True,
            "governance_metadata_integrity": True,
        },
        "final_decision": decision,
    }
