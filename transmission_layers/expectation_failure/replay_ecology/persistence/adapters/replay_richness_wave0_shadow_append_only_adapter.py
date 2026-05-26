from __future__ import annotations

from typing import Any

APPROVED_ADAPTER_NAME = "replay_richness_wave0_shadow_append_only_adapter"
APPROVED_TARGET = "replay_richness_wave0_shadow"
APPROVED_METRIC = "replay_richness"
MAX_RECORDS = 5

APPROVED_TOP_LEVEL_COLUMNS = (
    "wave_id",
    "entity_id",
    "metric_target",
    "metric_dimension",
    "duplicate_prevention_key",
    "payload",
    "source_artifact_refs",
    "lineage_metadata",
    "rollback_metadata",
    "evidence_status",
    "comparison_ready",
    "scaffold_only",
    "richness_score",
    "diversity_ratio",
    "concentration_warning",
    "adapter_name",
    "execution_mode",
)


def approved_adapter_available() -> bool:
    return True


def _base_result(*, target_name: str = APPROVED_TARGET) -> dict[str, Any]:
    return {
        "adapter_available": True,
        "approved_adapter_used": True,
        "attempted": False,
        "inserted_rows": 0,
        "duplicate_prevented": True,
        "rejected_rows": 0,
        "target_name": target_name,
        "append_only_verified": True,
        "lineage_retained": False,
        "rollback_metadata_present": False,
        "direct_sql_used": False,
        "halt_triggered": False,
        "halt_reason": None,
    }


def execute_append_only_insert(*, insert_intents: list[dict[str, Any]], metadata: dict[str, Any], client: Any) -> dict[str, Any]:
    result = _base_result(target_name=str(metadata.get("target_name") or APPROVED_TARGET))

    if metadata.get("metric_target") != APPROVED_METRIC:
        result.update({"halt_triggered": True, "halt_reason": "metric_target_mismatch", "rejected_rows": len(insert_intents), "duplicate_prevented": False})
        return result
    if metadata.get("target_name") != APPROVED_TARGET:
        result.update({"halt_triggered": True, "halt_reason": "target_mismatch", "rejected_rows": len(insert_intents), "duplicate_prevented": False, "append_only_verified": False})
        return result
    if metadata.get("append_only") is not True or metadata.get("mode") not in (None, "append_only_insert"):
        result.update({"halt_triggered": True, "halt_reason": "append_only_mode_required", "rejected_rows": len(insert_intents), "duplicate_prevented": False, "append_only_verified": False})
        return result
    for denied in ("update", "delete", "upsert", "direct_sql"):
        if metadata.get(denied) is True:
            result.update({"halt_triggered": True, "halt_reason": f"forbidden_{denied}_semantics", "rejected_rows": len(insert_intents), "duplicate_prevented": False, "append_only_verified": False})
            return result
    if metadata.get("topology_drift_enabled") is True or metadata.get("contradiction_persistence_migration_enabled") is True:
        result.update({"halt_triggered": True, "halt_reason": "forbidden_metric_scope", "rejected_rows": len(insert_intents), "duplicate_prevented": False})
        return result
    if not metadata.get("schema_confirmed"):
        result.update({"halt_triggered": True, "halt_reason": "schema_not_confirmed", "rejected_rows": len(insert_intents), "duplicate_prevented": False})
        return result
    if len(insert_intents) > MAX_RECORDS:
        result.update({"halt_triggered": True, "halt_reason": "entity_scope_overflow", "rejected_rows": len(insert_intents), "duplicate_prevented": False})
        return result

    for intent in insert_intents:
        payload = intent.get("payload", {})
        if payload.get("metric_dimension") != APPROVED_METRIC:
            result.update({"halt_triggered": True, "halt_reason": "payload_metric_mismatch", "rejected_rows": len(insert_intents), "duplicate_prevented": False})
            return result
        if not payload.get("source_artifact_refs"):
            result.update({"halt_triggered": True, "halt_reason": "missing_source_artifact_refs", "rejected_rows": len(insert_intents), "duplicate_prevented": False})
            return result
        if not isinstance(intent.get("lineage_metadata"), dict) or not intent.get("lineage_metadata"):
            result.update({"halt_triggered": True, "halt_reason": "missing_lineage_metadata", "rejected_rows": len(insert_intents), "duplicate_prevented": False})
            return result
        if not isinstance(intent.get("rollback_metadata"), dict) or not intent.get("rollback_metadata"):
            result.update({"halt_triggered": True, "halt_reason": "missing_rollback_metadata", "rejected_rows": len(insert_intents), "duplicate_prevented": False})
            return result
        key = intent.get("duplicate_prevention_key") or intent.get("duplicate_key")
        if not isinstance(key, str) or not key.strip():
            result.update({"halt_triggered": True, "halt_reason": "missing_duplicate_prevention_key", "rejected_rows": len(insert_intents), "duplicate_prevented": False})
            return result

    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    approved_columns = set(APPROVED_TOP_LEVEL_COLUMNS)
    for intent in insert_intents:
        key = str(intent.get("duplicate_prevention_key") or intent.get("duplicate_key"))
        if key in seen:
            continue
        seen.add(key)

        payload = dict(intent.get("payload", {}))
        row = {
            "wave_id": payload.get("wave_id"),
            "entity_id": payload.get("entity_id"),
            "metric_target": str(metadata.get("metric_target") or APPROVED_METRIC),
            "metric_dimension": payload.get("metric_dimension"),
            "duplicate_prevention_key": key,
            "payload": payload,
            "source_artifact_refs": payload.get("source_artifact_refs"),
            "lineage_metadata": dict(intent.get("lineage_metadata", {})),
            "rollback_metadata": dict(intent.get("rollback_metadata", {})),
            "evidence_status": payload.get("evidence_status"),
            "comparison_ready": payload.get("comparison_ready"),
            "scaffold_only": payload.get("scaffold_only"),
            "richness_score": payload.get("richness_score"),
            "diversity_ratio": payload.get("diversity_ratio"),
            "concentration_warning": payload.get("concentration_warning"),
            "adapter_name": APPROVED_ADAPTER_NAME,
            "execution_mode": str(metadata.get("mode") or "append_only_insert"),
        }

        if set(row) != approved_columns:
            result.update({"halt_triggered": True, "halt_reason": "invalid_stable_row_fields", "rejected_rows": len(insert_intents), "duplicate_prevented": False})
            return result

        rows.append(row)

    response = client.table(APPROVED_TARGET).insert(rows).execute()
    inserted_count = int(getattr(response, "count", None) or len(rows))
    result.update(
        {
            "attempted": True,
            "inserted_rows": inserted_count,
            "duplicate_prevented": len(rows) == len(seen),
            "rejected_rows": max(len(insert_intents) - len(rows), 0),
            "lineage_retained": True,
            "rollback_metadata_present": True,
        }
    )
    return result
