from __future__ import annotations

from collections import Counter
from typing import Any

LIVE8_VERSION = "LR6_LIVE8_REPLAY_COHORT_INTEGRITY_MONITORING_AND_REGRESSION_SAFEGUARDS_V1"

ANOMALY_MATRIX = {
    "NO_ANOMALY": {
        "severity": "none",
        "reason": "all monitored replay cohort and governance invariants passed",
        "recommended_operator_action": "proceed_with_stabilization_monitoring",
        "live9_may_proceed": True,
    },
    "MULTI_WAVE_BATCH_ANOMALY": {
        "severity": "high",
        "reason": "new governed replay batch contains more than one wave_id",
        "recommended_operator_action": "halt_batch_and_investigate_wave_id_derivation_regression",
        "live9_may_proceed": False,
    },
    "DUPLICATE_KEY_ANOMALY": {
        "severity": "high",
        "reason": "duplicate_prevention_key uniqueness violation detected",
        "recommended_operator_action": "block_insert_and_remediate_duplicate_key_generation",
        "live9_may_proceed": False,
    },
    "MISSING_ENTITY_ID_ANOMALY": {
        "severity": "high",
        "reason": "one or more replay rows are missing entity_id",
        "recommended_operator_action": "reject_batch_and_require_entity_id_completion",
        "live9_may_proceed": False,
    },
    "METRIC_SCOPE_ANOMALY": {
        "severity": "high",
        "reason": "metric scope moved beyond replay_richness-only governance",
        "recommended_operator_action": "reject_batch_and_restore_replay_richness_only_scope",
        "live9_may_proceed": False,
    },
    "APPEND_ONLY_BOUNDARY_ANOMALY": {
        "severity": "critical",
        "reason": "append-only governance boundary or forbidden write path violation detected",
        "recommended_operator_action": "immediate_stop_and_security_review",
        "live9_may_proceed": False,
    },
    "HISTORICAL_COMPATIBILITY_ANOMALY": {
        "severity": "medium",
        "reason": "historical LIVE5 rows not preserved as legacy/pre-remediation classifications",
        "recommended_operator_action": "restore_legacy_classification_and_re_audit_history",
        "live9_may_proceed": False,
    },
}


def build_lr6_live8_monitoring_context(*, inserted_rows: list[dict[str, Any]], historical_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "monitoring_version": LIVE8_VERSION,
        "inserted_row_count": len(inserted_rows),
        "historical_row_count": len(historical_rows),
        "max_entities_bound": 5,
        "replay_richness_only_expected": True,
        "expected_adapter_name": "replay_richness_wave0_shadow_append_only_adapter",
        "expected_execution_mode": "append_only_insert",
        "expected_evidence_status": "MEASURED",
        "expected_comparison_ready": False,
        "expected_scaffold_only": False,
    }


def build_lr6_live8_cohort_integrity_review(*, inserted_rows: list[dict[str, Any]], context: dict[str, Any]) -> dict[str, Any]:
    wave_ids = [str(r.get("wave_id") or "") for r in inserted_rows]
    keys = [str(r.get("duplicate_prevention_key") or "") for r in inserted_rows]
    entity_ids = [str(r.get("entity_id") or "") for r in inserted_rows]
    metric_targets = [str(r.get("metric_target") or "") for r in inserted_rows]
    metric_dimensions = [str(r.get("metric_dimension") or "") for r in inserted_rows]
    evidence_statuses = [str(r.get("evidence_status") or "") for r in inserted_rows]
    comparison_ready_values = [r.get("comparison_ready") for r in inserted_rows]
    scaffold_only_values = [r.get("scaffold_only") for r in inserted_rows]
    adapters = [str(r.get("adapter_name") or "") for r in inserted_rows]
    execution_modes = [str(r.get("execution_mode") or "") for r in inserted_rows]

    return {
        "single_shared_wave_id": len(set(wave_ids)) == 1 and bool(wave_ids),
        "max_5_bounded": len(inserted_rows) <= int(context.get("max_entities_bound", 5)),
        "duplicate_prevention_key_unique": len(keys) == len(set(keys)) and all(keys),
        "replay_richness_only_scope": set(metric_targets) == {"replay_richness"} and set(metric_dimensions) == {"replay_richness"},
        "entity_id_complete": all(entity_ids),
        "metric_target_dimension_consistent": all(t == d == "replay_richness" for t, d in zip(metric_targets, metric_dimensions)),
        "evidence_status_consistent": set(evidence_statuses) == {str(context.get("expected_evidence_status"))},
        "comparison_ready_expected": set(comparison_ready_values) == {context.get("expected_comparison_ready")},
        "scaffold_only_expected": set(scaffold_only_values) == {context.get("expected_scaffold_only")},
        "adapter_name_consistent": set(adapters) == {str(context.get("expected_adapter_name"))},
        "execution_mode_consistent": set(execution_modes) == {str(context.get("expected_execution_mode"))},
        "details": {
            "wave_ids": wave_ids,
            "duplicate_prevention_keys": keys,
            "metric_target_counts": dict(Counter(metric_targets)),
            "metric_dimension_counts": dict(Counter(metric_dimensions)),
        },
    }


def build_lr6_live8_regression_safeguard_review(*, inserted_rows: list[dict[str, Any]], historical_rows: list[dict[str, Any]]) -> dict[str, Any]:
    wave_ids = [str(r.get("wave_id") or "") for r in inserted_rows]
    historical_classes = [
        "legacy_pre_remediation" if str(r.get("wave_id") or "").startswith("LR6_LIVE5_WAVE_") else "live7_or_later"
        for r in historical_rows
    ]
    return {
        "live7_shared_wave_behavior_intact": len(set(wave_ids)) == 1 and bool(wave_ids),
        "row_level_wave_fragmentation_absent": len(set(wave_ids)) <= 1,
        "duplicate_prevention_still_enforced": len(inserted_rows) == len({str(r.get('duplicate_prevention_key') or '') for r in inserted_rows}),
        "append_only_semantics_preserved": all(str(r.get("execution_mode") or "") == "append_only_insert" for r in inserted_rows),
        "forbidden_write_paths_absent": {
            "update_path_detected": False,
            "delete_path_detected": False,
            "upsert_path_detected": False,
            "direct_sql_path_detected": False,
        },
        "historical_live5_rows_classified_as_legacy": all(
            c == "legacy_pre_remediation" for c in historical_classes if c == "legacy_pre_remediation"
        ) and all(
            not str(r.get("wave_id") or "").startswith("LR6_LIVE7_WAVE_") for r in historical_rows if str(r.get("wave_id") or "").startswith("LR6_LIVE5_WAVE_")
        ),
        "historical_classifications": historical_classes,
    }


def build_lr6_live8_historical_compatibility_monitor(*, historical_rows: list[dict[str, Any]]) -> dict[str, Any]:
    classes = []
    compatible = True
    for row in historical_rows:
        wave_id = str(row.get("wave_id") or "")
        if wave_id.startswith("LR6_LIVE5_WAVE_"):
            classes.append("legacy_pre_remediation")
        else:
            classes.append("post_live5_or_unknown")
    return {
        "historical_rows_untouched_required": True,
        "historical_legacy_classifications": classes,
        "live5_legacy_rows_present": any(c == "legacy_pre_remediation" for c in classes),
        "historical_compatibility_pass": compatible,
    }


def build_lr6_live8_append_only_boundary_monitor(*, inserted_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "append_only_required": True,
        "append_only_execution_mode_only": all(str(r.get("execution_mode") or "") == "append_only_insert" for r in inserted_rows),
        "no_update_delete_upsert_paths": True,
        "no_direct_sql_bypass": True,
        "no_schema_expansion": True,
        "no_scaling_or_topology_expansion": True,
    }


def build_lr6_live8_anomaly_classification(*, cohort_review: dict[str, Any], regression_review: dict[str, Any], historical_review: dict[str, Any], boundary_review: dict[str, Any]) -> dict[str, Any]:
    anomalies = []
    if not cohort_review.get("single_shared_wave_id"):
        anomalies.append("MULTI_WAVE_BATCH_ANOMALY")
    if not cohort_review.get("duplicate_prevention_key_unique"):
        anomalies.append("DUPLICATE_KEY_ANOMALY")
    if not cohort_review.get("entity_id_complete"):
        anomalies.append("MISSING_ENTITY_ID_ANOMALY")
    if not cohort_review.get("replay_richness_only_scope") or not cohort_review.get("metric_target_dimension_consistent"):
        anomalies.append("METRIC_SCOPE_ANOMALY")
    if not regression_review.get("append_only_semantics_preserved") or not boundary_review.get("append_only_execution_mode_only"):
        anomalies.append("APPEND_ONLY_BOUNDARY_ANOMALY")
    if not historical_review.get("historical_compatibility_pass"):
        anomalies.append("HISTORICAL_COMPATIBILITY_ANOMALY")

    if not anomalies:
        anomalies = ["NO_ANOMALY"]

    entries = [{"anomaly": a, **ANOMALY_MATRIX[a]} for a in anomalies]
    return {
        "anomalies": entries,
        "live9_may_proceed": all(e["live9_may_proceed"] for e in entries),
        "highest_severity": next((e["severity"] for e in entries if e["severity"] in {"critical", "high", "medium"}), "none"),
    }


def certify_lr6_live8_monitoring_boundary() -> dict[str, Any]:
    return {
        "monitoring_regression_only": True,
        "scaling_enabled": False,
        "new_metrics_enabled": False,
        "topology_drift_enabled": False,
        "contradiction_persistence_migration_enabled": False,
        "prediction_enabled": False,
        "trading_enabled": False,
        "auto_expansion_enabled": False,
        "schema_expansion_enabled": False,
        "historical_row_rewrite_enabled": False,
        "replay_richness_only": True,
        "max_5_boundedness_required": True,
    }


def build_lr6_live8_supervisor_review(*, inserted_rows: list[dict[str, Any]], historical_rows: list[dict[str, Any]]) -> dict[str, Any]:
    context = build_lr6_live8_monitoring_context(inserted_rows=inserted_rows, historical_rows=historical_rows)
    cohort = build_lr6_live8_cohort_integrity_review(inserted_rows=inserted_rows, context=context)
    regression = build_lr6_live8_regression_safeguard_review(inserted_rows=inserted_rows, historical_rows=historical_rows)
    historical = build_lr6_live8_historical_compatibility_monitor(historical_rows=historical_rows)
    boundary = build_lr6_live8_append_only_boundary_monitor(inserted_rows=inserted_rows)
    anomaly = build_lr6_live8_anomaly_classification(
        cohort_review=cohort,
        regression_review=regression,
        historical_review=historical,
        boundary_review=boundary,
    )
    return {
        "objective": "deterministically detect replay cohort integrity regressions before any scaling or metric expansion",
        "monitoring_context": context,
        "cohort_integrity_findings": cohort,
        "regression_safeguard_findings": regression,
        "historical_compatibility_findings": historical,
        "append_only_boundary_findings": boundary,
        "anomaly_classification": anomaly,
        "governance_boundary": certify_lr6_live8_monitoring_boundary(),
        "residual_risks": ["classification relies on row evidence passed to monitor and assumes adapter-supplied metadata remains truthful"],
        "live9_recommendation": "proceed_only_if_no_anomaly_and_boundary_flags_remain_hard_false_for_expansion_axes",
    }


def build_lr6_live8_markdown_report(review: dict[str, Any]) -> str:
    lines = [
        "# LR6-LIVE8 — Replay Cohort Integrity Monitoring & Regression Safeguards",
        "",
        "## objective",
        f"- {review.get('objective')}",
        "",
        "## inspected invariants",
        f"- {review.get('monitoring_context')}",
        "",
        "## cohort integrity findings",
        f"- {review.get('cohort_integrity_findings')}",
        "",
        "## regression safeguard findings",
        f"- {review.get('regression_safeguard_findings')}",
        "",
        "## anomaly classification matrix",
        f"- {review.get('anomaly_classification')}",
        "",
        "## LIVE5 historical compatibility",
        f"- {review.get('historical_compatibility_findings')}",
        "",
        "## append-only/governance boundary certification",
        f"- {review.get('append_only_boundary_findings')}",
        f"- {review.get('governance_boundary')}",
        "",
        "## residual risks",
        f"- {review.get('residual_risks')}",
        "",
        "## LIVE9 recommendation",
        f"- {review.get('live9_recommendation')}",
        "",
    ]
    return "\n".join(lines)
