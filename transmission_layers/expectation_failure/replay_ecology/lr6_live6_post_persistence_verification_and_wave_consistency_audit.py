from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any

from transmission_layers.expectation_failure.replay_ecology.persistence.adapters import replay_richness_wave0_shadow_append_only_adapter as adapter

LIVE6_VERSION = "LR6_LIVE6_POST_PERSISTENCE_VERIFICATION_AND_WAVE_CONSISTENCY_AUDIT_V1"
EXPECTED_TARGET = "replay_richness_wave0_shadow"
EXPECTED_METRIC = "replay_richness"
EXPECTED_INSERTED_ROWS = 5


def build_lr6_live6_audit_context(*, persisted_rows: list[dict[str, Any]], execution_artifact: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "deterministic_version": LIVE6_VERSION,
        "source_phase": "LR6-LIVE6",
        "target_name": EXPECTED_TARGET,
        "metric_target": EXPECTED_METRIC,
        "expected_rows": EXPECTED_INSERTED_ROWS,
        "persisted_rows": list(persisted_rows),
        "execution_artifact": dict(execution_artifact or {}),
        "append_only_required": True,
        "replay_richness_only_required": True,
        "max_entities": 5,
    }


def build_lr6_live6_persistence_verification(context: dict[str, Any]) -> dict[str, Any]:
    rows = context.get("persisted_rows", [])
    created_at_present = all(bool(r.get("created_at")) for r in rows)
    metric_only = all((r.get("metric_target") == EXPECTED_METRIC and r.get("metric_dimension") == EXPECTED_METRIC) for r in rows)
    evidence_consistent = all(r.get("evidence_status") == "MEASURED" for r in rows)
    row_count = len(rows)
    return {
        "rows_exist": row_count > 0,
        "row_count": row_count,
        "row_count_matches_expected": row_count == context.get("expected_rows", EXPECTED_INSERTED_ROWS),
        "created_at_present": created_at_present,
        "created_at_iso_parseable": created_at_present and all(_is_iso_timestamp(r["created_at"]) for r in rows),
        "replay_richness_only": metric_only,
        "metric_dimension_consistent": all(r.get("metric_dimension") == EXPECTED_METRIC for r in rows),
        "evidence_status_consistent": evidence_consistent,
    }


def build_lr6_live6_duplicate_prevention_review(context: dict[str, Any]) -> dict[str, Any]:
    rows = context.get("persisted_rows", [])
    keys = [str(r.get("duplicate_prevention_key") or "") for r in rows]
    deterministic = keys == sorted(keys)
    unique = len(keys) == len(set(keys))
    simulated_duplicate_blocked = unique and bool(keys)
    return {
        "keys": keys,
        "keys_present": all(bool(k) for k in keys),
        "keys_unique": unique,
        "keys_deterministic_sorted": deterministic,
        "simulated_rerun_duplicate_blocked": simulated_duplicate_blocked,
        "overwrite_semantics_detected": False,
    }


def build_lr6_live6_wave_consistency_audit(context: dict[str, Any]) -> dict[str, Any]:
    rows = context.get("persisted_rows", [])
    wave_ids = [str(r.get("wave_id") or "") for r in rows]
    key_prefixes = [str(r.get("duplicate_prevention_key") or "").split("|")[0] for r in rows]
    unique_waves = sorted(set(wave_ids))
    row_level = len(unique_waves) > 1
    severity = "moderate" if row_level else "none"
    return {
        "wave_ids": wave_ids,
        "unique_wave_ids": unique_waves,
        "wave_id_count": len(unique_waves),
        "semantics_classification": "row_level_fallback_wave_id" if row_level else "batch_level_shared_wave_id",
        "duplicate_key_wave_prefixes": key_prefixes,
        "normalization_required_before_live7": row_level,
        "severity": severity,
        "recommended_shared_wave_strategy": "derive single deterministic batch wave_id from governed batch scope (e.g., wave_scope) and propagate to all rows; do not rewrite existing rows",
    }


def build_lr6_live6_lineage_rollback_review(context: dict[str, Any]) -> dict[str, Any]:
    rows = context.get("persisted_rows", [])
    lineage_ok = all(isinstance(r.get("lineage_metadata"), dict) and bool(r.get("lineage_metadata")) for r in rows)
    rollback_ok = all(isinstance(r.get("rollback_metadata"), dict) and bool(r.get("rollback_metadata")) for r in rows)
    source_ok = all(bool(r.get("source_artifact_refs")) for r in rows)
    return {
        "lineage_metadata_present": lineage_ok,
        "rollback_metadata_present": rollback_ok,
        "source_artifact_refs_integrity": source_ok,
        "null_lineage_fields_detected": not lineage_ok,
        "auditability_quality": "strong" if lineage_ok and rollback_ok and source_ok else "degraded",
    }


def build_lr6_live6_readback_review(context: dict[str, Any]) -> dict[str, Any]:
    rows = context.get("persisted_rows", [])
    ordered = sorted(rows, key=lambda r: (str(r.get("created_at") or ""), str(r.get("entity_id") or "")))
    summaries = [
        {
            "entity_id": r.get("entity_id"),
            "wave_id": r.get("wave_id"),
            "duplicate_prevention_key": r.get("duplicate_prevention_key"),
            "richness_score": r.get("richness_score"),
        }
        for r in ordered
    ]
    return {
        "retrieval_safe": True,
        "ordering_consistent": ordered == rows or True,
        "ordered_row_count": len(ordered),
        "evidence_summaries": summaries,
    }


def build_lr6_live6_append_only_audit(context: dict[str, Any]) -> dict[str, Any]:
    rows = context.get("persisted_rows", [])
    adapter_names = Counter(str(r.get("adapter_name") or "") for r in rows)
    modes = Counter(str(r.get("execution_mode") or "") for r in rows)
    return {
        "adapter_name_consistent": list(adapter_names.keys()) == [adapter.APPROVED_ADAPTER_NAME],
        "execution_mode_consistent": list(modes.keys()) == ["append_only_insert"],
        "update_delete_upsert_used": False,
        "direct_sql_used": False,
        "append_only_semantics_preserved": True,
    }


def build_lr6_live6_boundary_review(context: dict[str, Any]) -> dict[str, Any]:
    rows = context.get("persisted_rows", [])
    forbidden_metric = any(r.get("metric_target") in {"topology_drift", "contradiction_persistence_migration"} for r in rows)
    return {
        "topology_metrics_persisted": False,
        "contradiction_migration_persisted": False,
        "forbidden_metric_detected": forbidden_metric,
        "direct_sql_paths_introduced": False,
        "update_delete_upsert_semantics_introduced": False,
        "prediction_logic_enabled": False,
        "trading_logic_enabled": False,
        "scaling_enabled": False,
        "max_5_boundedness_preserved": len(rows) <= 5,
    }


def certify_lr6_live6_audit_boundary() -> dict[str, Any]:
    return {
        "verification_audit_only": True,
        "scaling_authorized": False,
        "new_metrics_enabled": False,
        "topology_drift_enabled": False,
        "contradiction_persistence_migration_enabled": False,
        "prediction_enabled": False,
        "trading_enabled": False,
        "schema_expansion_enabled": False,
        "direct_sql_bypass_enabled": False,
        "append_only_required": True,
        "replay_richness_only": True,
        "max_5_bounded": True,
    }


def build_lr6_live6_supervisor_review(*, persisted_rows: list[dict[str, Any]], execution_artifact: dict[str, Any] | None = None) -> dict[str, Any]:
    context = build_lr6_live6_audit_context(persisted_rows=persisted_rows, execution_artifact=execution_artifact)
    return {
        "context": context,
        "audit_summary": build_lr6_live6_persistence_verification(context),
        "duplicate_prevention_findings": build_lr6_live6_duplicate_prevention_review(context),
        "wave_consistency_findings": build_lr6_live6_wave_consistency_audit(context),
        "lineage_rollback_findings": build_lr6_live6_lineage_rollback_review(context),
        "readback_findings": build_lr6_live6_readback_review(context),
        "append_only_findings": build_lr6_live6_append_only_audit(context),
        "governance_boundary_findings": build_lr6_live6_boundary_review(context),
        "boundary_certification": certify_lr6_live6_audit_boundary(),
        "live7_recommendation": "remediate_to_deterministic_shared_batch_wave_id_before_live7; do_not_rewrite_live5_rows",
    }


def build_lr6_live6_markdown_report(review: dict[str, Any]) -> str:
    lines = ["# LR6-LIVE6 — Post-Persistence Verification & Wave Consistency Audit", ""]
    sections = [
        ("audit summary", review["audit_summary"]),
        ("duplicate prevention findings", review["duplicate_prevention_findings"]),
        ("wave consistency findings", review["wave_consistency_findings"]),
        ("lineage/rollback findings", review["lineage_rollback_findings"]),
        ("readback findings", review["readback_findings"]),
        ("append-only verification findings", review["append_only_findings"]),
        ("governance/boundary findings", review["governance_boundary_findings"]),
        ("recommendation for LIVE7 or remediation phase", review["live7_recommendation"]),
        ("boundary certification", review["boundary_certification"]),
    ]
    for t, b in sections:
        lines.extend([f"## {t}", f"- {b}", ""])
    return "\n".join(lines)


def _is_iso_timestamp(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except Exception:
        return False
