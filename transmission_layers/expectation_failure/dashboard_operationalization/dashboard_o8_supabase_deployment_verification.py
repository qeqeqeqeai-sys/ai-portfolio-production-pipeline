"""Dashboard O8 deterministic Supabase deployment verification (read-only, injected-client only)."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from typing import Any, Mapping

from .dashboard_o6_supabase_read_adapter import (
    build_dashboard_read_column_inventory,
    build_dashboard_read_table_inventory,
)

SCHEMA_VERSION = "dashboard_o8_supabase_deployment_verification_v1"
MODULE_VERSION = "1.0.0"
_SAFE_MAX_SAMPLE_LIMIT = 5
_ALLOWED_STATUSES = ("verified", "degraded", "blocked", "invalid_client", "contract_mismatch")


def _clamp_sample_limit(sample_limit: int) -> int:
    limit = int(sample_limit) if isinstance(sample_limit, int) else 1
    if limit < 1:
        return 1
    return min(limit, _SAFE_MAX_SAMPLE_LIMIT)


def build_dashboard_o8_verification_scope() -> OrderedDict:
    tables = build_dashboard_read_table_inventory()
    columns = build_dashboard_read_column_inventory()
    return OrderedDict([
        ("schema_version", SCHEMA_VERSION),
        ("module_version", MODULE_VERSION),
        ("read_path", "dashboard_o6_supabase_read_adapter"),
        ("allowed_tables", tables),
        ("allowed_columns", columns),
        ("safe_max_sample_limit", _SAFE_MAX_SAMPLE_LIMIT),
        ("forbidden_operations", ["insert", "update", "delete", "upsert", "rpc", "raw_sql", "arbitrary_table_access", "unrestricted_column_access", "dashboard_triggered_mutation"]),
        ("status_values", list(_ALLOWED_STATUSES)),
    ])


def verify_dashboard_supabase_credentials(config_or_secrets) -> OrderedDict:
    cfg = deepcopy(dict(config_or_secrets or {})) if isinstance(config_or_secrets, Mapping) else {}
    url = str(cfg.get("supabase_url") or "").strip()
    key = str(cfg.get("supabase_key") or cfg.get("supabase_anon_key") or "").strip()
    present = bool(url and key)
    reasons = [] if present else ["missing_supabase_credentials"]
    return OrderedDict([
        ("status", "verified" if present else "degraded"),
        ("credentials_present", present),
        ("degraded_reasons", reasons),
    ])


def verify_dashboard_table_reachability(client, *, sample_limit=1) -> OrderedDict:
    safe_limit = _clamp_sample_limit(sample_limit)
    scope = build_dashboard_o8_verification_scope()
    checked = OrderedDict()
    degraded_reasons = []
    if client is None:
        return OrderedDict([
            ("status", "degraded"),
            ("checked_tables", checked),
            ("degraded_reasons", ["client_not_provided"]),
            ("applied_sample_limit", safe_limit),
        ])
    if not hasattr(client, "table"):
        return OrderedDict([
            ("status", "invalid_client"),
            ("checked_tables", checked),
            ("degraded_reasons", ["client_missing_table_method"]),
            ("applied_sample_limit", safe_limit),
        ])
    overall_status = "verified"
    for table_name in scope["allowed_tables"]:
        columns = scope["allowed_columns"][table_name]
        try:
            result = client.table(table_name).select(",".join(columns)).limit(safe_limit).execute()
            rows = list(getattr(result, "data", []) or [])
            checked[table_name] = OrderedDict([("reachable", True), ("row_count", len(rows))])
        except Exception as exc:
            checked[table_name] = OrderedDict([("reachable", False), ("error", f"{type(exc).__name__}: {str(exc)[:200]}")])
            degraded_reasons.append(f"table_unreachable:{table_name}")
            overall_status = "blocked"
    return OrderedDict([
        ("status", overall_status),
        ("checked_tables", checked),
        ("degraded_reasons", degraded_reasons),
        ("applied_sample_limit", safe_limit),
    ])


def verify_dashboard_column_contracts(client, *, sample_limit=1) -> OrderedDict:
    safe_limit = _clamp_sample_limit(sample_limit)
    scope = build_dashboard_o8_verification_scope()
    checked = OrderedDict()
    reasons = []
    if client is None:
        return OrderedDict([
            ("status", "degraded"),
            ("checked_columns", checked),
            ("degraded_reasons", ["client_not_provided"]),
            ("applied_sample_limit", safe_limit),
        ])
    if not hasattr(client, "table"):
        return OrderedDict([
            ("status", "invalid_client"),
            ("checked_columns", checked),
            ("degraded_reasons", ["client_missing_table_method"]),
            ("applied_sample_limit", safe_limit),
        ])
    status = "verified"
    for table_name in scope["allowed_tables"]:
        expected = tuple(scope["allowed_columns"][table_name])
        try:
            result = client.table(table_name).select(",".join(expected)).limit(safe_limit).execute()
            rows = list(getattr(result, "data", []) or [])
            if rows:
                present = set(rows[0].keys())
                missing = [c for c in expected if c not in present]
            else:
                missing = []
            ok = len(missing) == 0
            checked[table_name] = OrderedDict([("expected_columns", list(expected)), ("missing_columns", missing), ("compatible", ok)])
            if not ok:
                status = "contract_mismatch"
                reasons.append(f"contract_mismatch:{table_name}")
        except Exception as exc:
            checked[table_name] = OrderedDict([("expected_columns", list(expected)), ("missing_columns", list(expected)), ("compatible", False), ("error", f"{type(exc).__name__}: {str(exc)[:200]}")])
            status = "blocked"
            reasons.append(f"column_check_blocked:{table_name}")
    return OrderedDict([
        ("status", status),
        ("checked_columns", checked),
        ("degraded_reasons", reasons),
        ("applied_sample_limit", safe_limit),
    ])


def run_dashboard_o8_deployment_smoke_test(client=None, config_or_secrets=None):
    creds = verify_dashboard_supabase_credentials(config_or_secrets)
    reach = verify_dashboard_table_reachability(client, sample_limit=1)
    contracts = verify_dashboard_column_contracts(client, sample_limit=1)
    scope = build_dashboard_o8_verification_scope()
    reasons = list(creds["degraded_reasons"]) + list(reach["degraded_reasons"]) + list(contracts["degraded_reasons"])
    if reach["status"] == "invalid_client" or contracts["status"] == "invalid_client":
        status = "invalid_client"
    elif contracts["status"] == "contract_mismatch":
        status = "contract_mismatch"
    elif "blocked" in {reach["status"], contracts["status"]}:
        status = "blocked"
    elif creds["status"] == "degraded" or "degraded" in {reach["status"], contracts["status"]}:
        status = "degraded"
    else:
        status = "verified"
    return OrderedDict([
        ("objective", "Deterministic deployment verification for read-only dashboard Supabase access via O6 certified path."),
        ("scope", scope),
        ("checked_tables", reach["checked_tables"]),
        ("checked_columns", contracts["checked_columns"]),
        ("read_path", scope["read_path"]),
        ("forbidden_operations", scope["forbidden_operations"]),
        ("status", status),
        ("findings", OrderedDict([("credentials", creds), ("table_reachability", reach["status"]), ("column_contracts", contracts["status"])])),
        ("degraded_reasons", reasons),
        ("invariants", OrderedDict([("read_only_verification_only", True), ("injected_client_only", True), ("no_writes", True), ("no_rpc", True), ("no_raw_sql", True), ("bounded_sample_reads_only", True), ("deterministic_output_shape", True), ("immutable_input_safe", True), ("additive_only", True)])),
        ("final_decision", "allow_dashboard_read_path" if status == "verified" else "degraded_or_blocked"),
    ])


def build_dashboard_o8_deployment_report_payload(result=None):
    materialized = run_dashboard_o8_deployment_smoke_test() if result is None else deepcopy(result)
    return OrderedDict([
        ("schema_version", SCHEMA_VERSION),
        ("module_version", MODULE_VERSION),
        ("objective", materialized["objective"]),
        ("scope", materialized["scope"]),
        ("checked_tables", materialized["checked_tables"]),
        ("checked_columns", materialized["checked_columns"]),
        ("read_path", materialized["read_path"]),
        ("forbidden_operations", materialized["forbidden_operations"]),
        ("status", materialized["status"]),
        ("findings", materialized["findings"]),
        ("degraded_reasons", materialized["degraded_reasons"]),
        ("invariants", materialized["invariants"]),
        ("final_decision", materialized["final_decision"]),
    ])


__all__ = [
    "build_dashboard_o8_verification_scope",
    "verify_dashboard_supabase_credentials",
    "verify_dashboard_table_reachability",
    "verify_dashboard_column_contracts",
    "run_dashboard_o8_deployment_smoke_test",
    "build_dashboard_o8_deployment_report_payload",
]
