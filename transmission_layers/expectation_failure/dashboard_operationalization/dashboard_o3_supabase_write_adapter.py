"""Deterministic Dashboard O3 Supabase write adapter and execution planning."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

from .dashboard_o2_supabase_contracts import build_dashboard_o2_upsert_payload

SCHEMA_VERSION = "dashboard_o3_supabase_write_adapter_v1"
MODULE_VERSION = "1.0.0"

FORBIDDEN_TERMS = (
    "buy", "sell", "short", "target price", "portfolio allocation", "backtesting", "predictive", "recommendation", "trade"
)

INVARIANT_FLAGS = OrderedDict([
    ("deterministic_only", True),
    ("injected_client_only", True),
    ("dry_run_default", True),
    ("no_hardcoded_credentials", True),
    ("no_env_access", True),
    ("no_file_writes", True),
    ("no_streamlit_ui", True),
    ("no_uncontrolled_network_calls", True),
    ("validation_before_write", True),
    ("no_trading_recommendations", True),
    ("immutable_input_safe", True),
])

MAX_ERROR_MESSAGE_LENGTH = 200
SENSITIVE_SUBSTRINGS = ("apikey", "api_key", "authorization", "bearer", "token", "secret", "password", "supabase_")


def _stable_checksum(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _contains_forbidden_language(value: Any) -> bool:
    if isinstance(value, str):
        low = value.lower()
        return any(term in low for term in FORBIDDEN_TERMS)
    if isinstance(value, Mapping):
        return any(_contains_forbidden_language(v) for v in value.values())
    if isinstance(value, list):
        return any(_contains_forbidden_language(v) for v in value)
    return False


def _sanitize_and_truncate_error_message(message: str, *, limit: int = MAX_ERROR_MESSAGE_LENGTH) -> str:
    sanitized = message
    for marker in SENSITIVE_SUBSTRINGS:
        sanitized = sanitized.replace(marker, "[redacted]")
        sanitized = sanitized.replace(marker.upper(), "[REDACTED]")
    return sanitized[:limit]


def _classify_error_type(message: str) -> str:
    low = message.lower()
    if any(k in low for k in ("row-level security", "rls", "permission denied", "not authorized", "forbidden", "401", "403")):
        return "rls_or_policy_failure"
    if any(k in low for k in ("not null", "null value", "missing required")):
        return "not_null_constraint"
    if any(k in low for k in ("duplicate key", "unique constraint", "primary key", "conflict")):
        return "primary_key_or_unique_conflict"
    if any(k in low for k in ("invalid input syntax", "invalid type", "datatype mismatch", "cannot cast", "type")):
        return "invalid_data_type"
    if any(k in low for k in ("column", "does not exist", "unknown column", "schema cache")):
        return "column_mismatch"
    if any(k in low for k in ("upsert", "insert", "supabase")):
        return "supabase_insert_upsert_api_error"
    return "unknown_write_error"


def _extract_row_count_from_response(response: Any, attempted: int) -> int | None:
    data = getattr(response, "data", None)
    if isinstance(data, list):
        return len(data)
    if isinstance(data, Mapping):
        return 1
    if isinstance(response, Mapping):
        payload = response.get("data")
        if isinstance(payload, list):
            return len(payload)
        if isinstance(payload, Mapping):
            return 1
    return attempted


def _build_table_diagnostics(step: Mapping[str, Any], *, status: str, attempted_row_count: int, inserted_count: int | None = None, error: Exception | None = None) -> OrderedDict:
    rows = list(step.get("rows", []))
    payload_keys = sorted({k for r in rows if isinstance(r, Mapping) for k in r.keys()})
    expected_cols = list(step.get("schema_expected_columns", []))
    expected_required = list(step.get("schema_required_columns", []))
    missing_required = sorted([k for k in expected_required if k not in payload_keys])
    extra_cols = sorted([k for k in payload_keys if expected_cols and k not in expected_cols])
    error_type = None
    error_short = None
    if error is not None:
        raw = f"{type(error).__name__}: {str(error)}"
        error_short = _sanitize_and_truncate_error_message(raw)
        error_type = _classify_error_type(raw)
    return OrderedDict([
        ("table_name", step["table_name"]),
        ("status", status),
        ("planned_row_count", int(step.get("row_count", 0))),
        ("attempted_row_count", int(attempted_row_count)),
        ("inserted_or_affected_row_count", inserted_count),
        ("error_type", error_type),
        ("error_message_short", error_short),
        ("missing_payload_columns", missing_required),
        ("extra_payload_columns", extra_cols),
        ("schema_expected_columns", expected_cols),
        ("payload_sample_keys", payload_keys[:12]),
        ("on_conflict", step.get("on_conflict")),
    ])


def build_dashboard_o3_write_plan(o2_upsert_payload: Mapping[str, Any], *, execution_mode: str = "dry_run", dry_run: bool = True) -> OrderedDict:
    source = deepcopy(dict(o2_upsert_payload))
    normalized_o2 = build_dashboard_o2_upsert_payload(source) if "upsert_batches" not in source else source
    validation_summary = normalized_o2.get("validation_summary", {})
    if validation_summary.get("validation_status") != "valid":
        return OrderedDict([
            ("schema_version", SCHEMA_VERSION),
            ("module_version", MODULE_VERSION),
            ("execution_mode", execution_mode),
            ("dry_run", bool(dry_run)),
            ("write_steps", []),
            ("validation_summary", OrderedDict([
                ("validation_status", "invalid"),
                ("errors", ["o2 payload validation failed before write-plan build"] + list(validation_summary.get("errors", []))),
            ])),
            ("write_plan_checksum", ""),
            ("invariant_flags", deepcopy(INVARIANT_FLAGS)),
        ])

    contract_index = {c["table_name"]: c for c in normalized_o2.get("table_contracts", [])}
    write_steps = []
    for idx, batch in enumerate(normalized_o2.get("upsert_batches", []), start=1):
        step = OrderedDict([
            ("step_sequence", idx),
            ("table_name", batch["table_name"]),
            ("source_payload_key", batch["source_payload_key"]),
            ("unique_key", list(batch["unique_key"])),
            ("on_conflict", ",".join(batch["unique_key"])),
            ("rows", deepcopy(list(batch.get("rows", [])))),
            ("row_count", int(batch.get("row_count", 0))),
            ("deterministic_sort_key", list(batch.get("deterministic_sort_key", []))),
            ("persistence_mode", batch.get("persistence_mode", "upsert")),
            ("schema_expected_columns", list(contract_index.get(batch["table_name"], {}).get("columns", []))),
            ("schema_required_columns", list(contract_index.get(batch["table_name"], {}).get("required_columns", []))),
            ("execution_mode", execution_mode),
            ("dry_run", bool(dry_run)),
        ])
        step["step_checksum"] = _stable_checksum(step)
        write_steps.append(step)

    plan = OrderedDict([
        ("schema_version", SCHEMA_VERSION),
        ("module_version", MODULE_VERSION),
        ("execution_mode", execution_mode),
        ("dry_run", bool(dry_run)),
        ("write_steps", write_steps),
        ("validation_summary", OrderedDict([("validation_status", "valid"), ("errors", [])])),
        ("invariant_flags", deepcopy(INVARIANT_FLAGS)),
    ])
    plan["write_plan_checksum"] = _stable_checksum(plan)
    return plan


def validate_dashboard_o3_write_plan(write_plan: Mapping[str, Any]) -> OrderedDict:
    plan = deepcopy(dict(write_plan))
    errors = []
    for key in ["schema_version", "module_version", "execution_mode", "dry_run", "write_steps", "invariant_flags"]:
        if key not in plan:
            errors.append(f"missing top-level key: {key}")

    mode = plan.get("execution_mode")
    dry_run = bool(plan.get("dry_run", True))
    if mode not in {"dry_run", "execute"}:
        errors.append("invalid execution_mode")
    if mode == "dry_run" and dry_run is not True:
        errors.append("dry_run mode requires dry_run=True")
    if mode == "execute" and dry_run is True:
        errors.append("execute mode requires dry_run=False")

    steps = plan.get("write_steps", [])
    if not isinstance(steps, list):
        errors.append("write_steps must be a list")
        steps = []

    for step in steps:
        for key in ["table_name", "unique_key", "rows", "row_count", "persistence_mode"]:
            if key not in step:
                errors.append(f"missing write step key: {key}")
        rows = step.get("rows", [])
        unique_key = list(step.get("unique_key", []))
        if int(step.get("row_count", -1)) != len(rows):
            errors.append(f"row_count mismatch for table {step.get('table_name', 'unknown')}")
        if len(unique_key) != len(set(unique_key)):
            errors.append(f"duplicate unique key field in table {step.get('table_name', 'unknown')}")
        if _contains_forbidden_language(step):
            errors.append(f"forbidden language detected in table {step.get('table_name', 'unknown')}")

    status = "valid" if not errors else "invalid"
    return OrderedDict([
        ("validation_status", status),
        ("error_count", len(errors)),
        ("errors", errors),
    ])


def execute_dashboard_o3_write_plan(write_plan: Mapping[str, Any], supabase_client: Any | None = None) -> OrderedDict:
    plan = deepcopy(dict(write_plan))
    validation = validate_dashboard_o3_write_plan(plan)
    if validation["validation_status"] != "valid":
        return OrderedDict([
            ("execution_status", "validation_failed"),
            ("validation_summary", validation),
            ("table_results", []),
            ("checksum", _stable_checksum(OrderedDict([("validation", validation), ("write_plan_checksum", plan.get("write_plan_checksum", ""))]))),
        ])

    dry_run = bool(plan.get("dry_run", True))
    mode = plan.get("execution_mode", "dry_run")
    table_results = []

    if mode == "execute" and dry_run is False and supabase_client is None:
        return OrderedDict([
            ("execution_status", "failed"),
            ("validation_summary", validation),
            ("table_results", []),
            ("errors", ["execute mode requires injected supabase_client"]),
            ("checksum", _stable_checksum("missing_client")),
        ])

    for step in plan.get("write_steps", []):
        if dry_run or mode == "dry_run":
            table_results.append(_build_table_diagnostics(step, status="skipped", attempted_row_count=0, inserted_count=0))
            continue

        try:
            response = supabase_client.table(step["table_name"]).upsert(step["rows"], on_conflict=step["on_conflict"]).execute()
            inserted = _extract_row_count_from_response(response, int(step.get("row_count", 0)))
            table_results.append(_build_table_diagnostics(step, status="success", attempted_row_count=int(step.get("row_count", 0)), inserted_count=inserted))
        except Exception as exc:  # bounded adapter-level exception capture
            table_results.append(_build_table_diagnostics(step, status="failed", attempted_row_count=int(step.get("row_count", 0)), inserted_count=0, error=exc))

    status = "completed"
    checksum = _stable_checksum(OrderedDict([("results", table_results), ("write_plan_checksum", plan.get("write_plan_checksum", ""))]))
    return OrderedDict([
        ("execution_status", status),
        ("validation_summary", validation),
        ("table_results", table_results),
        ("checksum", checksum),
    ])


def build_dashboard_o3_write_result_manifest(write_plan: Mapping[str, Any], execution_result: Mapping[str, Any]) -> OrderedDict:
    plan = deepcopy(dict(write_plan))
    result = deepcopy(dict(execution_result))
    table_results = list(result.get("table_results", []))
    counts = OrderedDict([
        ("success", sum(1 for r in table_results if r.get("status") == "success")),
        ("failed", sum(1 for r in table_results if r.get("status") == "failed")),
        ("simulated", sum(1 for r in table_results if r.get("status") == "simulated")),
        ("skipped", sum(1 for r in table_results if r.get("status") == "skipped")),
    ])
    manifest = OrderedDict([
        ("schema_version", SCHEMA_VERSION),
        ("module_version", MODULE_VERSION),
        ("execution_mode", plan.get("execution_mode", "dry_run")),
        ("dry_run", bool(plan.get("dry_run", True))),
        ("table_count", len(plan.get("write_steps", []))),
        ("total_row_count", sum(int(s.get("row_count", 0)) for s in plan.get("write_steps", []))),
        ("successful_table_count", counts["success"] + counts["simulated"]),
        ("failed_table_count", counts["failed"]),
        ("skipped_table_count", counts["skipped"]),
        ("table_result_counts", counts),
        ("validation_status", result.get("validation_summary", {}).get("validation_status", "invalid")),
        ("invariant_flags", deepcopy(INVARIANT_FLAGS)),
    ])
    manifest["checksum"] = _stable_checksum(manifest)
    return manifest


def build_dashboard_o3_dry_run_report(write_plan: Mapping[str, Any], execution_result: Mapping[str, Any]) -> OrderedDict:
    plan = deepcopy(dict(write_plan))
    result = deepcopy(dict(execution_result))
    return OrderedDict([
        ("schema_version", SCHEMA_VERSION),
        ("module_version", MODULE_VERSION),
        ("planned_tables", [s.get("table_name") for s in plan.get("write_steps", [])]),
        ("planned_row_counts", OrderedDict((s.get("table_name"), int(s.get("row_count", 0))) for s in plan.get("write_steps", []))),
        ("dry_run", bool(plan.get("dry_run", True))),
        ("execution_mode", plan.get("execution_mode", "dry_run")),
        ("validation_status", result.get("validation_summary", {}).get("validation_status", "invalid")),
        ("invariant_flags", deepcopy(INVARIANT_FLAGS)),
    ])


def build_dashboard_o3_persistence_audit_report(write_plan: Mapping[str, Any], execution_result: Mapping[str, Any]) -> OrderedDict:
    plan = deepcopy(dict(write_plan))
    result = deepcopy(dict(execution_result))
    failed_tables = [r for r in result.get("table_results", []) if r.get("status") == "failed"]
    report = OrderedDict([
        ("schema_version", SCHEMA_VERSION),
        ("module_version", MODULE_VERSION),
        ("execution_summary", OrderedDict([
            ("execution_mode", plan.get("execution_mode", "dry_run")),
            ("dry_run", bool(plan.get("dry_run", True))),
            ("table_count", len(plan.get("write_steps", []))),
            ("failed_table_count", len(failed_tables)),
        ])),
        ("failed_tables", failed_tables),
        ("validation_findings", result.get("validation_summary", OrderedDict())),
        ("checksum", _stable_checksum(OrderedDict([("plan", plan.get("write_plan_checksum", "")), ("result", result.get("checksum", ""))]))),
        ("boundaries", deepcopy(INVARIANT_FLAGS)),
    ])
    return report


__all__ = [
    "build_dashboard_o3_write_plan",
    "validate_dashboard_o3_write_plan",
    "execute_dashboard_o3_write_plan",
    "build_dashboard_o3_write_result_manifest",
    "build_dashboard_o3_dry_run_report",
    "build_dashboard_o3_persistence_audit_report",
]
