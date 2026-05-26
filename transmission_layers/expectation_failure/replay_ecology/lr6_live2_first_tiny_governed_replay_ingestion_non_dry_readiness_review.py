"""LR6-LIVE2 first tiny governed replay ingestion non-dry readiness review (review-only)."""
from __future__ import annotations

from typing import Any

DETERMINISTIC_VERSION = "LR6_LIVE2_FIRST_TINY_GOVERNED_REPLAY_INGESTION_NON_DRY_READINESS_REVIEW_V1"
TARGET_METRIC = "replay_richness"
READINESS_CLASSES = [
    "blocked",
    "not_ready",
    "conditionally_ready_for_tiny_non_dry_execution",
    "ready_but_requires_explicit_operator_approval",
]


def build_lr6_live2_readiness_context(live1_wave_summary: dict[str, Any] | None = None) -> dict[str, Any]:
    sample = {
        "governance_passed": True,
        "halt_triggered": False,
        "critical_halt_count": 0,
        "payloads_prepared": 5,
        "payloads_rejected": 0,
        "rejected_payloads_safely_quarantined": True,
        "unsafe_promotion_count": 0,
        "duplicate_prevention_keys_deterministic": True,
        "append_only_simulation_passed": True,
        "shadow_persistence_simulation_passed": True,
        "rollback_ready": True,
        "lineage_complete": True,
        "isolated_persistence_target_adequate": True,
        "metric_dimensions": [TARGET_METRIC],
        "entity_count": 5,
        "persisted": False,
        "dry_run_only": True,
        "explicit_non_dry_operator_approval_required": True,
    }
    return {
        "deterministic_version": DETERMINISTIC_VERSION,
        "source_phase": "LR6-LIVE2",
        "scope": "non_dry_readiness_review_only",
        "execution_authorized": False,
        "persistence_authorized": False,
        "live_ingestion_authorized": False,
        "governed_activation_authorized": False,
        "live1_wave_summary": live1_wave_summary or sample,
    }


def build_lr6_live2_live1_dry_run_result_review(context: dict[str, Any]) -> dict[str, Any]:
    s = context["live1_wave_summary"]
    checks = {
        "dry_run_only": s.get("dry_run_only") is True,
        "persisted_false": s.get("persisted") is False,
        "payloads_prepared_positive": isinstance(s.get("payloads_prepared"), int) and s.get("payloads_prepared", 0) > 0,
        "entity_count_bounded": isinstance(s.get("entity_count"), int) and s.get("entity_count", 999) <= 5,
        "metric_scope_replay_richness_only": s.get("metric_dimensions") == [TARGET_METRIC],
    }
    return {"checks": checks, "passed": all(checks.values())}


def build_lr6_live2_governance_pass_review(context: dict[str, Any]) -> dict[str, Any]:
    s = context["live1_wave_summary"]
    passed = s.get("governance_passed") is True
    return {"governance_passed": passed, "review_status": "pass" if passed else "fail"}


def build_lr6_live2_halt_trigger_review(context: dict[str, Any]) -> dict[str, Any]:
    s = context["live1_wave_summary"]
    no_halt = s.get("halt_triggered") is False and s.get("critical_halt_count", 0) == 0
    return {"halt_triggered": s.get("halt_triggered") is True, "critical_halt_count": s.get("critical_halt_count", 0), "passed": no_halt}


def build_lr6_live2_payload_validity_review(context: dict[str, Any]) -> dict[str, Any]:
    s = context["live1_wave_summary"]
    rejected = s.get("payloads_rejected", 0)
    quarantined = s.get("rejected_payloads_safely_quarantined", False)
    passed = s.get("payloads_prepared", 0) > 0 and (rejected == 0 or quarantined)
    return {"payloads_prepared": s.get("payloads_prepared", 0), "payloads_rejected": rejected, "rejected_payloads_safely_quarantined": quarantined, "passed": passed}


def build_lr6_live2_duplicate_key_review(context: dict[str, Any]) -> dict[str, Any]:
    v = context["live1_wave_summary"].get("duplicate_prevention_keys_deterministic") is True
    return {"duplicate_prevention_keys_deterministic": v, "passed": v}


def build_lr6_live2_append_only_readiness_review(context: dict[str, Any]) -> dict[str, Any]:
    v = context["live1_wave_summary"].get("append_only_simulation_passed") is True
    return {"append_only_simulation_passed": v, "passed": v}


def build_lr6_live2_shadow_persistence_readiness_review(context: dict[str, Any]) -> dict[str, Any]:
    s = context["live1_wave_summary"]
    v = s.get("shadow_persistence_simulation_passed") is True and s.get("persisted") is False
    return {"shadow_persistence_simulation_passed": s.get("shadow_persistence_simulation_passed") is True, "persisted": s.get("persisted"), "passed": v}


def build_lr6_live2_rollback_readiness_review(context: dict[str, Any]) -> dict[str, Any]:
    v = context["live1_wave_summary"].get("rollback_ready") is True
    return {"rollback_ready": v, "passed": v}


def build_lr6_live2_lineage_readiness_review(context: dict[str, Any]) -> dict[str, Any]:
    s = context["live1_wave_summary"]
    v = s.get("lineage_complete") is True and s.get("isolated_persistence_target_adequate") is True
    return {"lineage_complete": s.get("lineage_complete") is True, "isolated_persistence_target_adequate": s.get("isolated_persistence_target_adequate") is True, "passed": v}


def build_lr6_live2_non_dry_gate_requirements() -> dict[str, Any]:
    return {
        "explicit_approval_phrase": "I APPROVE LR6-LIVE NON-DRY TINY REPLAY EXECUTION",
        "non_dry_execution_token": "LR6_LIVE_NON_DRY_TINY_EXECUTION_TOKEN_REQUIRED",
        "append_only_confirmation_required": True,
        "isolated_persistence_target_confirmation_required": True,
        "rollback_metadata_confirmation_required": True,
        "lineage_completeness_confirmation_required": True,
        "metric_whitelist_confirmation": [TARGET_METRIC],
        "entity_limit_confirmation_max": 5,
        "halt_on_first_error_confirmation_required": True,
        "duplicate_prevention_key_confirmation_required": True,
        "dry_run_success_evidence_reference_required": "LR6-LIVE1 first tiny governed replay ingestion dry-run wave evidence",
        "explicit_non_dry_operator_approval_required": True,
    }


def build_lr6_live2_non_dry_readiness_recommendation(context: dict[str, Any]) -> dict[str, Any]:
    s = context["live1_wave_summary"]
    critical_conditions = [
        s.get("governance_passed") is True,
        s.get("halt_triggered") is False,
        s.get("critical_halt_count", 0) == 0,
        s.get("payloads_prepared", 0) > 0,
        (s.get("payloads_rejected", 0) == 0) or (s.get("rejected_payloads_safely_quarantined") is True),
        s.get("unsafe_promotion_count", 0) == 0,
        s.get("duplicate_prevention_keys_deterministic") is True,
        s.get("append_only_simulation_passed") is True,
        s.get("shadow_persistence_simulation_passed") is True,
        s.get("rollback_ready") is True,
        s.get("lineage_complete") is True,
        s.get("metric_dimensions") == [TARGET_METRIC],
        isinstance(s.get("entity_count"), int) and s.get("entity_count") <= 5,
        s.get("persisted") is False,
        s.get("dry_run_only") is True,
        s.get("explicit_non_dry_operator_approval_required") is True,
    ]
    if not s.get("governance_passed") or s.get("critical_halt_count", 0) > 0 or s.get("unsafe_promotion_count", 0) > 0:
        readiness_classification = "blocked"
    elif all(critical_conditions):
        readiness_classification = "conditionally_ready_for_tiny_non_dry_execution"
    else:
        readiness_classification = "not_ready"

    return {
        "readiness_classification": readiness_classification,
        "execution_authorized": False,
        "persistence_authorized": False,
        "live_ingestion_authorized": False,
        "governed_activation_authorized": False,
        "explicit_non_dry_operator_approval_required": True,
        "later_phase_only_recommendation": readiness_classification in {"conditionally_ready_for_tiny_non_dry_execution", "ready_but_requires_explicit_operator_approval"},
    }


def certify_lr6_live2_readiness_boundary() -> dict[str, Any]:
    return {
        "non_dry_readiness_review_only": True,
        "execution_authorized": False,
        "persistence_authorized": False,
        "live_ingestion_authorized": False,
        "governed_activation_authorized": False,
        "metric_target": TARGET_METRIC,
        "max_entities": 5,
        "all_seven_metrics_implemented": False,
        "no_prediction": True,
        "no_trading": True,
        "no_direct_sql": True,
        "no_live_ingestion": True,
        "no_persistence_write": True,
        "no_governed_activation": True,
        "architecture_expansion_frozen": True,
    }


def build_lr6_live2_supervisor_review(live1_wave_summary: dict[str, Any] | None = None) -> dict[str, Any]:
    context = build_lr6_live2_readiness_context(live1_wave_summary)
    return {
        "objective": "Determine whether LR6-LIVE1 dry-run outcomes justify conditional eligibility review for a later tiny governed non-dry execution phase.",
        "inspected_paths": [
            "lr6_live1_first_tiny_governed_replay_ingestion_dry_run_wave.py",
            "lr6_live0_governed_live_replay_ingestion_readiness_plan.py",
            "lr6_evid14_first_replay_richness_payload_supervisor_review.py",
            "lr6_evid13_dry_run_replay_richness_payload_attachment.py",
            "lr6_evid12_real_replay_richness_payload_validation_harness.py",
            "lr6_evid11_first_real_replay_richness_payload_builder.py",
            "lr6_evid6_minimal_in_memory_metrics_emission_hook.py",
        ],
        "context": context,
        "live1_dry_run_result_review": build_lr6_live2_live1_dry_run_result_review(context),
        "governance_pass_review": build_lr6_live2_governance_pass_review(context),
        "halt_trigger_review": build_lr6_live2_halt_trigger_review(context),
        "payload_validity_review": build_lr6_live2_payload_validity_review(context),
        "duplicate_key_review": build_lr6_live2_duplicate_key_review(context),
        "append_only_readiness_review": build_lr6_live2_append_only_readiness_review(context),
        "shadow_persistence_readiness_review": build_lr6_live2_shadow_persistence_readiness_review(context),
        "rollback_readiness_review": build_lr6_live2_rollback_readiness_review(context),
        "lineage_readiness_review": build_lr6_live2_lineage_readiness_review(context),
        "non_dry_gate_requirements": build_lr6_live2_non_dry_gate_requirements(),
        "non_dry_readiness_recommendation": build_lr6_live2_non_dry_readiness_recommendation(context),
        "boundary_certification": certify_lr6_live2_readiness_boundary(),
        "realism_warning": "This review is fail-closed and non-authorizing; no execution, writes, or governed activation are permitted in LR6-LIVE2.",
        "supervisor_decision": "KEEP_NON_DRY_EXECUTION_BLOCKED_PENDING_EXPLICIT_OPERATOR_APPROVAL_IN_LATER_PHASE",
    }


def build_lr6_live2_markdown_report(live1_wave_summary: dict[str, Any] | None = None) -> str:
    r = build_lr6_live2_supervisor_review(live1_wave_summary)
    return "\n".join([
        "# LR6-LIVE2 — First Tiny Governed Replay Ingestion Non-Dry Readiness Review",
        "",
        "## objective",
        f"- {r['objective']}",
        "",
        "## inspected LIVE1/LIVE0/EVID paths",
        f"- {r['inspected_paths']}",
        "",
        "## LIVE1 dry-run result review",
        f"- {r['live1_dry_run_result_review']}",
        "",
        "## governance pass review",
        f"- {r['governance_pass_review']}",
        "",
        "## halt trigger review",
        f"- {r['halt_trigger_review']}",
        "",
        "## payload validity review",
        f"- {r['payload_validity_review']}",
        "",
        "## duplicate key review",
        f"- {r['duplicate_key_review']}",
        "",
        "## append-only readiness review",
        f"- {r['append_only_readiness_review']}",
        "",
        "## shadow persistence readiness review",
        f"- {r['shadow_persistence_readiness_review']}",
        "",
        "## rollback readiness review",
        f"- {r['rollback_readiness_review']}",
        "",
        "## lineage readiness review",
        f"- {r['lineage_readiness_review']}",
        "",
        "## non-dry gate requirements",
        f"- {r['non_dry_gate_requirements']}",
        "",
        "## non-dry readiness recommendation",
        f"- {r['non_dry_readiness_recommendation']}",
        "",
        "## supervisor decision",
        f"- {r['supervisor_decision']}",
        "",
        "## realism warning",
        f"- {r['realism_warning']}",
        "",
        "## boundary certification",
        f"- {r['boundary_certification']}",
        "",
        "## recommendation for next step",
        "- Keep non-dry execution blocked in LIVE2; if and only if operator approvals are explicitly recorded later, proceed to a separate constrained execution phase.",
    ])
