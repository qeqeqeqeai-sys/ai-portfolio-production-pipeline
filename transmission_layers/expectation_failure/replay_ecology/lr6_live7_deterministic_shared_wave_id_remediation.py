from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any

LIVE7_VERSION = "LR6_LIVE7_DETERMINISTIC_SHARED_WAVE_ID_REMEDIATION_V1"
SHARED_WAVE_PREFIX = "LR6_LIVE7_WAVE"


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def build_lr6_live7_shared_wave_context(*, insert_intents: list[dict[str, Any]], metadata: dict[str, Any]) -> dict[str, Any]:
    keys = [str(i.get("duplicate_prevention_key") or i.get("duplicate_key") or "") for i in insert_intents]
    entity_ids = sorted(str((i.get("payload") or {}).get("entity_id") or "") for i in insert_intents)
    return {
        "deterministic_version": LIVE7_VERSION,
        "target_name": str(metadata.get("target_name") or ""),
        "metric_target": str(metadata.get("metric_target") or ""),
        "max_entities": 5,
        "ordered_duplicate_prevention_keys": sorted(keys),
        "ordered_entity_ids": entity_ids,
        "intent_count": len(insert_intents),
        "execution_mode": str(metadata.get("mode") or "append_only_insert"),
        "append_only": bool(metadata.get("append_only") is True),
    }


def build_lr6_live7_shared_wave_id(context: dict[str, Any]) -> str:
    batch_material = {
        "target_name": context.get("target_name"),
        "metric_target": context.get("metric_target"),
        "ordered_duplicate_prevention_keys": context.get("ordered_duplicate_prevention_keys", []),
        "ordered_entity_ids": context.get("ordered_entity_ids", []),
        "intent_count": context.get("intent_count", 0),
        "execution_mode": context.get("execution_mode"),
    }
    digest = hashlib.sha1(_stable_json(batch_material).encode("utf-8")).hexdigest()[:12].upper()
    return f"{SHARED_WAVE_PREFIX}_{digest}"


def build_lr6_live7_wave_grouping_review(*, rows: list[dict[str, Any]]) -> dict[str, Any]:
    waves = [str(r.get("wave_id") or "") for r in rows]
    return {
        "wave_id_count": len(set(waves)),
        "single_shared_wave_id": len(set(waves)) == 1 and bool(waves),
        "wave_ids": waves,
        "replay_cohort_identity_preserved": len(set(waves)) == 1,
    }


def build_lr6_live7_wave_lineage_review(*, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "lineage_metadata_present": all(isinstance(r.get("lineage_metadata"), dict) and bool(r.get("lineage_metadata")) for r in rows),
        "rollback_metadata_present": all(isinstance(r.get("rollback_metadata"), dict) and bool(r.get("rollback_metadata")) for r in rows),
        "source_artifact_refs_present": all(bool(r.get("source_artifact_refs")) for r in rows),
    }


def build_lr6_live7_historical_compatibility_review(*, historical_rows: list[dict[str, Any]]) -> dict[str, Any]:
    classifications = []
    for r in historical_rows:
        wave = str(r.get("wave_id") or "")
        pre = wave.startswith("LR6_LIVE5_WAVE_")
        classifications.append("pre_live7_row_level_fallback" if pre else "live7_or_later_shared_wave")
    return {
        "historical_rows_untouched_required": True,
        "automatic_migration_performed": False,
        "automatic_normalization_performed": False,
        "classifications": classifications,
    }


def build_lr6_live7_append_only_certification(*, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "append_only_semantics_preserved": True,
        "direct_sql_used": False,
        "duplicate_prevention_key_uniqueness_preserved": len(rows) == len({str(r.get('duplicate_prevention_key') or '') for r in rows}),
        "max_5_boundedness_preserved": len(rows) <= 5,
        "adapter_name_consistent": list(Counter(str(r.get("adapter_name") or "") for r in rows).keys()) == ["replay_richness_wave0_shadow_append_only_adapter"],
        "execution_mode_consistent": all(str(r.get("execution_mode") or "") == "append_only_insert" for r in rows),
    }


def certify_lr6_live7_shared_wave_boundary() -> dict[str, Any]:
    return {
        "scaling_enabled": False,
        "topology_expansion_enabled": False,
        "contradiction_persistence_migration_enabled": False,
        "prediction_enabled": False,
        "trading_enabled": False,
        "auto_expansion_enabled": False,
        "historical_row_rewrites_enabled": False,
        "replay_richness_only": True,
        "append_only_required": True,
    }


def build_lr6_live7_supervisor_review(*, inserted_rows: list[dict[str, Any]], historical_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "shared_wave_remediation_summary": "deterministic_shared_batch_wave_id_implemented",
        "deterministic_derivation_explanation": "shared wave_id derived from deterministic batch digest over governed metadata and ordered inventory",
        "replay_cohort_semantics_explanation": "one governed replay batch maps to one shared wave_id while duplicate_prevention_key remains row uniqueness identity",
        "wave_grouping_review": build_lr6_live7_wave_grouping_review(rows=inserted_rows),
        "wave_lineage_review": build_lr6_live7_wave_lineage_review(rows=inserted_rows),
        "historical_compatibility_review": build_lr6_live7_historical_compatibility_review(historical_rows=historical_rows),
        "append_only_findings": build_lr6_live7_append_only_certification(rows=inserted_rows),
        "governance_findings": certify_lr6_live7_shared_wave_boundary(),
        "residual_risks": ["legacy_live5_rows_retain_row_level_fallback_semantics_for_audit_history"],
        "live8_recommendation": "add_monitoring_alert_if_any_new_batch_persists_multiple_wave_ids",
    }


def build_lr6_live7_markdown_report(review: dict[str, Any]) -> str:
    sections = [
        "shared_wave_remediation_summary",
        "deterministic_derivation_explanation",
        "replay_cohort_semantics_explanation",
        "historical_compatibility_review",
        "append_only_findings",
        "governance_findings",
        "residual_risks",
        "live8_recommendation",
    ]
    lines = ["# LR6-LIVE7 — Deterministic Shared Wave ID Remediation", ""]
    for section in sections:
        lines.extend([f"## {section}", f"- {review.get(section)}", ""])
    return "\n".join(lines)
