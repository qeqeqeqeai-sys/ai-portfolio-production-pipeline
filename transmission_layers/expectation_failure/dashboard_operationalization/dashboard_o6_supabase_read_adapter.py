"""Deterministic Dashboard O6 Supabase read adapter (read-only, injected-client only)."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from typing import Any, Mapping

SCHEMA_VERSION = "dashboard_o6_supabase_read_adapter_v1"
MODULE_VERSION = "1.0.0"

_ALLOWED_TABLES = (
    "dashboard_entity_facts",
    "dashboard_subsector_facts",
    "dashboard_alert_facts",
    "dashboard_benchmark_facts",
    "dashboard_replay_facts",
    "dashboard_evidence_facts",
    "dashboard_certification_reports",
    "dashboard_run_manifests",
)

_TABLE_COLUMNS = OrderedDict([
    ("dashboard_entity_facts", ("run_id", "run_date_sgt", "entity_id", "entity_name", "ticker", "subsector", "composite_score", "relative_fragility_band", "alert_state", "benchmark_relative_label", "evidence_quality_flag", "certification_status", "replay_checksum")),
    ("dashboard_subsector_facts", ("run_id", "run_date_sgt", "subsector", "entity_count", "avg_composite_score", "fragile_entity_count", "alert_entity_count", "subsector_fragility_band", "evidence_quality_summary", "replay_checksum")),
    ("dashboard_alert_facts", ("run_id", "run_date_sgt", "entity_id", "ticker", "subsector", "alert_state", "alert_severity_band", "active_alert_flag", "dominant_alert_driver", "evidence_quality_flag", "replay_checksum")),
    ("dashboard_benchmark_facts", ("run_id", "run_date_sgt", "entity_id", "ticker", "subsector", "benchmark_id", "entity_fragility_score", "benchmark_fragility_score", "relative_gap", "relative_gap_band", "benchmark_relative_label", "outlier_flag", "replay_checksum")),
    ("dashboard_replay_facts", ("run_id", "replay_date_sgt", "entity_id", "ticker", "subsector", "composite_score", "fragility_band", "alert_state", "deterioration_label", "replay_sequence", "replay_checksum")),
    ("dashboard_evidence_facts", ("run_id", "run_date_sgt", "entity_id", "ticker", "evidence_id", "evidence_type", "source_metric", "source_value", "normalized_score", "quality_flag", "evidence_chain_position", "template_id", "replay_checksum")),
    ("dashboard_certification_reports", ("run_id", "run_date_sgt", "certification_status", "report_type", "export_manifest_checksum")),
    ("dashboard_run_manifests", ("run_id", "checksum", "run_date_sgt", "schema_version", "module_version")),
])

_MAX_LIMITS = {"default": 500, "replay": 200, "metadata": 100}


def _clamp_limit(limit: int, max_limit: int) -> int:
    bounded = int(limit) if isinstance(limit, int) else max_limit
    if bounded < 1:
        return 1
    return min(bounded, max_limit)


def _load_rows(client: Any, *, logical_table: str, run_id: str | None = None, as_of_date: str | None = None, entity_id: str | None = None, limit: int = 500) -> OrderedDict:
    safe_limit = _clamp_limit(limit, _MAX_LIMITS["default"])
    columns = tuple(_TABLE_COLUMNS[logical_table])
    degraded = OrderedDict([("table", logical_table), ("rows", []), ("row_count", 0), ("status", "degraded"), ("error", None), ("applied_limit", safe_limit)])

    if client is None:
        degraded["error"] = "client_not_provided"
        return degraded

    try:
        query = client.table(logical_table).select(",".join(columns))
        if run_id is not None:
            query = query.eq("run_id", run_id)
        if as_of_date is not None:
            query = query.eq("run_date_sgt", as_of_date)
        if entity_id is not None:
            query = query.eq("entity_id", entity_id)
        if "replay_sequence" in columns:
            query = query.order("replay_sequence", desc=False)
        query = query.order("run_id", desc=False).limit(safe_limit)
        result = query.execute()
        data = list(getattr(result, "data", []) or [])
        normalized = [OrderedDict((col, row.get(col)) for col in columns) for row in data if isinstance(row, Mapping)]
        return OrderedDict([("table", logical_table), ("rows", normalized), ("row_count", len(normalized)), ("status", "ok"), ("error", None), ("applied_limit", safe_limit)])
    except Exception as exc:
        degraded["error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
        return degraded


def build_dashboard_read_table_inventory() -> list[str]:
    return list(_ALLOWED_TABLES)


def build_dashboard_read_column_inventory() -> OrderedDict:
    return OrderedDict((k, list(v)) for k, v in _TABLE_COLUMNS.items())


def load_dashboard_entity_facts(client, *, run_id=None, as_of_date=None, limit=500):
    return _load_rows(client, logical_table="dashboard_entity_facts", run_id=run_id, as_of_date=as_of_date, limit=limit)


def load_dashboard_subsector_facts(client, *, run_id=None, as_of_date=None, limit=500):
    return _load_rows(client, logical_table="dashboard_subsector_facts", run_id=run_id, as_of_date=as_of_date, limit=limit)


def load_dashboard_alert_facts(client, *, run_id=None, as_of_date=None, limit=500):
    return _load_rows(client, logical_table="dashboard_alert_facts", run_id=run_id, as_of_date=as_of_date, limit=limit)


def load_dashboard_benchmark_facts(client, *, run_id=None, as_of_date=None, limit=500):
    return _load_rows(client, logical_table="dashboard_benchmark_facts", run_id=run_id, as_of_date=as_of_date, limit=limit)


def load_dashboard_replay_facts(client, *, run_id=None, limit=200):
    return _load_rows(client, logical_table="dashboard_replay_facts", run_id=run_id, limit=_clamp_limit(limit, _MAX_LIMITS["replay"]))


def load_dashboard_evidence_facts(client, *, run_id=None, entity_id=None, limit=500):
    return _load_rows(client, logical_table="dashboard_evidence_facts", run_id=run_id, entity_id=entity_id, limit=limit)


def load_dashboard_certification_metadata(client, *, run_id=None, limit=100):
    return _load_rows(client, logical_table="dashboard_certification_reports", run_id=run_id, limit=_clamp_limit(limit, _MAX_LIMITS["metadata"]))


def build_dashboard_supabase_snapshot(client, *, run_id=None, as_of_date=None):
    return OrderedDict([
        ("schema_version", SCHEMA_VERSION),
        ("module_version", MODULE_VERSION),
        ("table_inventory", build_dashboard_read_table_inventory()),
        ("column_inventory", build_dashboard_read_column_inventory()),
        ("entity_facts", load_dashboard_entity_facts(client, run_id=run_id, as_of_date=as_of_date)),
        ("subsector_facts", load_dashboard_subsector_facts(client, run_id=run_id, as_of_date=as_of_date)),
        ("alert_facts", load_dashboard_alert_facts(client, run_id=run_id, as_of_date=as_of_date)),
        ("benchmark_facts", load_dashboard_benchmark_facts(client, run_id=run_id, as_of_date=as_of_date)),
        ("replay_facts", load_dashboard_replay_facts(client, run_id=run_id)),
        ("evidence_facts", load_dashboard_evidence_facts(client, run_id=run_id)),
        ("certification_metadata", load_dashboard_certification_metadata(client, run_id=run_id)),
        ("invariant_flags", OrderedDict([("deterministic_only", True), ("injected_client_only", True), ("read_only", True), ("no_writes", True), ("bounded_queries", True), ("degraded_mode", True), ("immutable_input_safe", True), ("additive_only", True)])),
    ])


def build_dashboard_o6_read_adapter_report_payload():
    return OrderedDict([
        ("schema_version", SCHEMA_VERSION),
        ("module_version", MODULE_VERSION),
        ("objective", "Deterministic read-only Supabase adapter for dashboard O4/O5 stack."),
        ("allowed_tables", build_dashboard_read_table_inventory()),
        ("allowed_columns", build_dashboard_read_column_inventory()),
        ("forbidden_operations", ["insert", "update", "delete", "upsert", "rpc", "raw_sql", "arbitrary_table_access"]),
        ("degraded_mode", "Stable empty rows with status=degraded and bounded error string."),
    ])


__all__ = [
    "build_dashboard_read_table_inventory",
    "build_dashboard_read_column_inventory",
    "load_dashboard_entity_facts",
    "load_dashboard_subsector_facts",
    "load_dashboard_alert_facts",
    "load_dashboard_benchmark_facts",
    "load_dashboard_replay_facts",
    "load_dashboard_evidence_facts",
    "load_dashboard_certification_metadata",
    "build_dashboard_supabase_snapshot",
    "build_dashboard_o6_read_adapter_report_payload",
]
