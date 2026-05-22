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
            table_results.append(OrderedDict([
                ("table_name", step["table_name"]),
                ("status", "simulated"),
                ("row_count", step["row_count"]),
                ("on_conflict", step["on_conflict"]),
                ("error", None),
            ]))
            continue

        try:
            supabase_client.table(step["table_name"]).upsert(step["rows"], on_conflict=step["on_conflict"]).execute()
            table_results.append(OrderedDict([
                ("table_name", step["table_name"]),
                ("status", "success"),
                ("row_count", step["row_count"]),
                ("on_conflict", step["on_conflict"]),
                ("error", None),
            ]))
        except Exception as exc:  # bounded adapter-level exception capture
            table_results.append(OrderedDict([
                ("table_name", step["table_name"]),
                ("status", "failed"),
                ("row_count", step["row_count"]),
                ("on_conflict", step["on_conflict"]),
                ("error", f"{type(exc).__name__}: {str(exc)[:200]}"),
            ]))

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
