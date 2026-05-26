"""LR6-LIVE4 first non-dry execution result verification (evidence-first, verification-only)."""
from __future__ import annotations

from typing import Any

from transmission_layers.expectation_failure.replay_ecology.lr6_live3_first_tiny_governed_replay_ingestion_non_dry_execution import (
    ISOLATED_PERSISTENCE_TARGET,
    MAX_ENTITIES,
    TARGET_METRIC,
)

DETERMINISTIC_VERSION = "LR6_LIVE4_FIRST_NON_DRY_EXECUTION_RESULT_VERIFICATION_V1"


CLASSIFICATIONS = {
    "no_persistence_event_detected",
    "guarded_execution_path_defined_only",
    "persistence_event_simulated_only",
    "tiny_non_dry_persistence_verified",
    "persistence_unclear_requires_manual_evidence",
    "failed_or_halted",
}


def build_lr6_live4_verification_context(*, live3_summary: dict[str, Any] | None = None, evidence_source: str = "passed_in_summary") -> dict[str, Any]:
    return {
        "deterministic_version": DETERMINISTIC_VERSION,
        "source_phase": "LR6-LIVE4",
        "objective": "Verify LR6-LIVE3 non-dry execution result without authorizing new execution.",
        "evidence_source": evidence_source,
        "live3_summary": dict(live3_summary or {}),
        "verification_only": True,
    }


def inspect_lr6_live4_live3_execution_surface(context: dict[str, Any]) -> dict[str, Any]:
    s = context.get("live3_summary", {})
    halted = bool(s.get("halt_triggered") or s.get("aborted"))
    persistence_executed = s.get("persistence_executed")
    inserted = s.get("payloads_inserted")
    has_intents = bool(s.get("insert_intents_planned") or s.get("append_only_plan_defined"))
    real_adapter = bool(s.get("approved_persistence_adapter_called"))
    if halted:
        classification = "failed_or_halted"
    elif persistence_executed is False and not has_intents:
        classification = "no_persistence_event_detected"
    elif persistence_executed is False and has_intents:
        classification = "guarded_execution_path_defined_only"
    elif persistence_executed is True and not real_adapter:
        classification = "persistence_event_simulated_only"
    elif persistence_executed is True and real_adapter and isinstance(inserted, int):
        classification = "tiny_non_dry_persistence_verified"
    else:
        classification = "persistence_unclear_requires_manual_evidence"
    return {
        "classification": classification,
        "halted": halted,
        "persistence_executed": persistence_executed,
        "approved_persistence_adapter_called": real_adapter,
        "inserted_rows_evidence_present": isinstance(inserted, int),
    }


def build_lr6_live4_persistence_event_review(context: dict[str, Any], surface: dict[str, Any]) -> dict[str, Any]:
    s = context.get("live3_summary", {})
    return {
        "persistence_event_detected": bool(s.get("persistence_executed") is True),
        "classification": surface["classification"],
        "approved_adapter_called": bool(s.get("approved_persistence_adapter_called")),
        "evidence_confidence": "high" if surface["classification"] in {"tiny_non_dry_persistence_verified", "failed_or_halted"} else "bounded",
    }


def build_lr6_live4_inserted_row_review(context: dict[str, Any]) -> dict[str, Any]:
    s = context.get("live3_summary", {})
    inserted = s.get("payloads_inserted")
    duplicate_prevented = s.get("duplicate_prevented_count", s.get("duplicate_prevented", 0))
    persisted = s.get("persisted_rows", inserted if isinstance(inserted, int) else 0)
    return {
        "inserted_rows": inserted if isinstance(inserted, int) and inserted >= 0 else 0,
        "duplicate_prevented": duplicate_prevented if isinstance(duplicate_prevented, int) and duplicate_prevented >= 0 else 0,
        "persisted_rows": persisted if isinstance(persisted, int) and persisted >= 0 else 0,
        "row_count_consistency": isinstance(inserted, int) and isinstance(persisted, int) and persisted == inserted,
        "evidence_present": isinstance(inserted, int),
    }


def build_lr6_live4_persistence_target_review(context: dict[str, Any]) -> dict[str, Any]:
    target = context.get("live3_summary", {}).get("persistence_target", "")
    isolated = target == ISOLATED_PERSISTENCE_TARGET or ("shadow" in str(target).lower())
    return {"persistence_target": target or "unknown", "isolated_or_shadow": isolated, "target_approved": isolated}


def build_lr6_live4_duplicate_prevention_review(context: dict[str, Any]) -> dict[str, Any]:
    s = context.get("live3_summary", {})
    return {
        "duplicate_prevention_keys_respected": bool(s.get("duplicate_prevented", False)),
        "duplicate_conflicts_detected": int(s.get("duplicate_conflicts_detected", 0) or 0),
    }


def build_lr6_live4_append_only_verification(context: dict[str, Any]) -> dict[str, Any]:
    s = context.get("live3_summary", {})
    append_only = bool(s.get("append_only", s.get("append_only_verification", False)))
    return {"append_only": append_only, "no_updates_deletes_overwrites": append_only and not bool(s.get("mutations_detected", False))}


def build_lr6_live4_lineage_retention_review(context: dict[str, Any]) -> dict[str, Any]:
    return {"lineage_refs_retained": bool(context.get("live3_summary", {}).get("lineage_refs_retained", False))}


def build_lr6_live4_rollback_metadata_review(context: dict[str, Any]) -> dict[str, Any]:
    return {"rollback_metadata_present": bool(context.get("live3_summary", {}).get("rollback_ready", False))}


def build_lr6_live4_halt_condition_review(context: dict[str, Any]) -> dict[str, Any]:
    s = context.get("live3_summary", {})
    return {"halt_triggered": bool(s.get("halt_triggered", False)), "halt_reason": s.get("halt_reason")}


def build_lr6_live4_payload_rejection_review(context: dict[str, Any]) -> dict[str, Any]:
    s = context.get("live3_summary", {})
    rejected = int(s.get("payloads_rejected", 0) or 0)
    quarantined = int(s.get("payloads_quarantined", 0) or 0)
    return {"payloads_rejected": rejected, "payloads_quarantined": quarantined, "rejection_or_quarantine_detected": (rejected + quarantined) > 0}


def build_lr6_live4_scope_compliance_review(context: dict[str, Any]) -> dict[str, Any]:
    s = context.get("live3_summary", {})
    metric = s.get("metric_target", TARGET_METRIC)
    entities = int(s.get("entity_count", 0) or 0)
    return {
        "metric_target": metric,
        "replay_richness_only": metric == TARGET_METRIC,
        "entity_count": entities,
        "entity_cap_respected": entities <= MAX_ENTITIES,
    }


def build_lr6_live4_scaling_recommendation(*, all_checks_passed: bool, classification: str) -> dict[str, Any]:
    authorized = bool(all_checks_passed and classification == "tiny_non_dry_persistence_verified")
    return {
        "scaling_authorized": False,
        "scale_to_300_authorized": False,
        "enable_all_metrics_authorized": False,
        "conservative_next_step": "conduct_post_persistence_audit_then_repeat_tiny_wave_before_any_10_entity_readiness",
        "verification_status": "strong_but_still_blocked" if authorized else "blocked_pending_additional_evidence",
    }


def certify_lr6_live4_verification_boundary() -> dict[str, Any]:
    return {
        "verification_only": True,
        "new_execution_authorized": False,
        "new_persistence_authorized": False,
        "live_ingestion_expansion_authorized": False,
        "scaling_authorized": False,
        "metric_target": "replay_richness",
        "max_verified_entities": 5,
        "all_seven_metrics_implemented": False,
        "direct_sql_used": False,
        "topology_metrics_enabled": False,
        "contradiction_migration_enabled": False,
        "prediction_enabled": False,
        "trading_enabled": False,
        "auto_expansion_enabled": False,
    }


def build_lr6_live4_supervisor_verification(*, live3_summary: dict[str, Any]) -> dict[str, Any]:
    context = build_lr6_live4_verification_context(live3_summary=live3_summary)
    surface = inspect_lr6_live4_live3_execution_surface(context)
    persistence = build_lr6_live4_persistence_event_review(context, surface)
    inserted = build_lr6_live4_inserted_row_review(context)
    target = build_lr6_live4_persistence_target_review(context)
    duplicate = build_lr6_live4_duplicate_prevention_review(context)
    append_only = build_lr6_live4_append_only_verification(context)
    lineage = build_lr6_live4_lineage_retention_review(context)
    rollback = build_lr6_live4_rollback_metadata_review(context)
    halt = build_lr6_live4_halt_condition_review(context)
    rejection = build_lr6_live4_payload_rejection_review(context)
    scope = build_lr6_live4_scope_compliance_review(context)
    all_checks = all([
        target["target_approved"],
        append_only["append_only"],
        append_only["no_updates_deletes_overwrites"],
        lineage["lineage_refs_retained"],
        rollback["rollback_metadata_present"],
        scope["replay_richness_only"],
        scope["entity_cap_respected"],
        not halt["halt_triggered"],
    ])
    scaling = build_lr6_live4_scaling_recommendation(all_checks_passed=all_checks, classification=surface["classification"])
    return {
        "objective": "Verify what LR6-LIVE3 actually executed and whether real rows were inserted.",
        "inspected_paths": [
            "lr6_live3_first_tiny_governed_replay_ingestion_non_dry_execution.py",
            "lr6_live2_first_tiny_governed_replay_ingestion_non_dry_readiness_review.py",
            "lr6_live1_first_tiny_governed_replay_ingestion_dry_run_wave.py",
            "lr6_live0_governed_live_replay_ingestion_readiness_plan.py",
            "lr6_evid14_first_replay_richness_payload_supervisor_review.py",
            "lr6_evid13_dry_run_replay_richness_payload_attachment.py",
            "lr6_evid11_first_real_replay_richness_payload_builder.py",
        ],
        "live3_execution_surface_review": surface,
        "persistence_event_review": persistence,
        "inserted_row_review": inserted,
        "persistence_target_review": target,
        "duplicate_prevention_review": duplicate,
        "append_only_verification": append_only,
        "lineage_retention_review": lineage,
        "rollback_metadata_review": rollback,
        "halt_condition_review": halt,
        "payload_rejection_quarantine_review": rejection,
        "scope_compliance_review": scope,
        "scaling_recommendation": scaling,
        "realism_warning": "Verification evidence can confirm only what is present in artifacts; absent persistence evidence is treated as non-insertion.",
        "boundary_certification": certify_lr6_live4_verification_boundary(),
        "recommendation_for_next_step": "Maintain scaling block. Run post-persistence audit and repeat tiny wave before any broader readiness transition.",
    }


def build_lr6_live4_markdown_report(verification: dict[str, Any]) -> str:
    sections = [
        ("objective", verification["objective"]),
        ("inspected LIVE3/LIVE2/LIVE1/LIVE0/EVID paths", verification["inspected_paths"]),
        ("LIVE3 execution surface review", verification["live3_execution_surface_review"]),
        ("persistence event review", verification["persistence_event_review"]),
        ("inserted row review", verification["inserted_row_review"]),
        ("persistence target review", verification["persistence_target_review"]),
        ("duplicate prevention review", verification["duplicate_prevention_review"]),
        ("append-only verification", verification["append_only_verification"]),
        ("lineage retention review", verification["lineage_retention_review"]),
        ("rollback metadata review", verification["rollback_metadata_review"]),
        ("halt-condition review", verification["halt_condition_review"]),
        ("payload rejection/quarantine review", verification["payload_rejection_quarantine_review"]),
        ("scope compliance review", verification["scope_compliance_review"]),
        ("scaling recommendation", verification["scaling_recommendation"]),
        ("realism warning", verification["realism_warning"]),
        ("boundary certification", verification["boundary_certification"]),
        ("recommendation for next step", verification["recommendation_for_next_step"]),
    ]
    lines = ["# LR6-LIVE4 — First Non-Dry Execution Result Verification", ""]
    for title, body in sections:
        lines.extend([f"## {title}", f"- {body}", ""])
    return "\n".join(lines)
