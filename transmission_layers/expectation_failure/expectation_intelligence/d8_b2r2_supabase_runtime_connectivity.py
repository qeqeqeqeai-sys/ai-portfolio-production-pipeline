from __future__ import annotations

from collections import OrderedDict
from hashlib import sha256
from typing import Any, Mapping
import os

from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o7_streamlit_supabase_runtime import (
    build_streamlit_supabase_runtime_config,
    resolve_streamlit_supabase_client,
)

READ_ONLY_TABLES = (
    "dashboard_replay_metadata_records",
    "dashboard_export_manifests",
)

ACCEPTED_SUPABASE_KEY_ENV_NAMES = (
    "SUPABASE_SERVICE_ROLE_KEY",
    "SUPABASE_ANON_KEY",
    "SUPABASE_KEY",
)


def _t(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _fingerprint(value: str | None) -> str | None:
    token = _t(value)
    if not token:
        return None
    return f"sha256:{sha256(token.encode('utf-8')).hexdigest()[:12]}"


def _resolve_key_source(env: Mapping[str, str]) -> str:
    for name in ACCEPTED_SUPABASE_KEY_ENV_NAMES:
        if _t(env.get(name)):
            return f"env:{name}"
    return "missing"


def audit_supabase_runtime_credentials(*, env: Mapping[str, str] | None = None, runtime_config: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    e = dict(env or os.environ)
    cfg = OrderedDict(runtime_config or build_streamlit_supabase_runtime_config())
    url = _t(cfg.get("supabase_url"))
    key = _t(cfg.get("supabase_key"))

    if not url:
        url = _t(e.get("SUPABASE_URL"))
    if not key:
        for name in ACCEPTED_SUPABASE_KEY_ENV_NAMES:
            key = _t(e.get(name))
            if key:
                break

    url_present = bool(url)
    key_present = bool(key)
    if url_present and key_present:
        status = "CREDENTIALS_READY"
    elif url_present or key_present:
        status = "CREDENTIALS_PARTIAL"
    else:
        status = "CREDENTIALS_MISSING"

    return OrderedDict([
        ("status", status),
        ("credentials_present", status == "CREDENTIALS_READY"),
        ("supabase_url_present", url_present),
        ("supabase_key_present", key_present),
        ("supabase_url_source", _t(cfg.get("supabase_url_source")) or ("env:SUPABASE_URL" if url_present else "missing")),
        ("supabase_key_source", _t(cfg.get("supabase_key_source")) or _resolve_key_source(e)),
        ("supabase_url_fingerprint", _fingerprint(url)),
        ("supabase_key_fingerprint", _fingerprint(key)),
        ("accepted_env_var_names", ["SUPABASE_URL", *ACCEPTED_SUPABASE_KEY_ENV_NAMES]),
    ])


def audit_supabase_read_only_connectivity(*, credential_audit: Mapping[str, Any], runtime_config: Mapping[str, Any] | None = None, client: Any = None, client_factory: Any = None, tables: tuple[str, ...] = READ_ONLY_TABLES) -> OrderedDict[str, Any]:
    cfg = OrderedDict(runtime_config or build_streamlit_supabase_runtime_config())
    cfg["credentials_present"] = bool(credential_audit.get("credentials_present"))

    if not credential_audit.get("credentials_present"):
        return OrderedDict([
            ("client_status", "CLIENT_UNRESOLVED"),
            ("read_only_connectivity_status", "READ_ONLY_CONNECTIVITY_NOT_ATTEMPTED"),
            ("selected_key_source", _t(credential_audit.get("supabase_key_source")) or "missing"),
            ("create_client_import_status", "not_attempted"),
            ("client_exception_class", None),
            ("client_exception_short_message", None),
            ("connectivity_exception_class", None),
            ("connectivity_exception_short_message", None),
            ("blocked_category", "client_construction_failure"),
            ("resolved_client_factory_source", "unavailable"),
            ("blocked_reason", "CREDENTIALS_MISSING"),
            ("table_probe", []),
        ])

    resolution = resolve_streamlit_supabase_client(cfg, client=client, client_factory=client_factory)
    if not resolution.get("client_resolved"):
        return OrderedDict([
            ("client_status", "CLIENT_UNRESOLVED"),
            ("read_only_connectivity_status", "READ_ONLY_CONNECTIVITY_BLOCKED"),
            ("selected_key_source", _t(credential_audit.get("supabase_key_source")) or "missing"),
            ("create_client_import_status", "ok" if resolution.get("supabase_package_available") else "failed"),
            ("client_exception_class", resolution.get("client_error_type")),
            ("client_exception_short_message", resolution.get("client_error_message_short")),
            ("connectivity_exception_class", None),
            ("connectivity_exception_short_message", None),
            ("blocked_category", "client_construction_failure"),
            ("resolved_client_factory_source", _t(resolution.get("client_factory_source")) or "unavailable"),
            ("blocked_reason", "CLIENT_UNRESOLVED"),
            ("table_probe", []),
        ])

    probe = []
    try:
        c = resolution.get("client")
        for table in tables:
            resp = c.table(table).select("id", count="exact").limit(1).execute()
            count = getattr(resp, "count", None)
            if count is None:
                data = getattr(resp, "data", [])
                count = len(data) if isinstance(data, list) else 0
            probe.append(OrderedDict([("table", table), ("ok", True), ("count", int(count))]))
    except Exception as exc:
        msg = str(exc).lower()
        category = "connectivity_failure"
        if any(x in msg for x in ("not authorized", "jwt", "401", "invalid api key", "auth")):
            category = "auth_failure"
        elif any(x in msg for x in ("permission", "forbidden", "rls", "42501", "403")):
            category = "permission_failure"
        elif any(x in msg for x in ("schema", "3f000")):
            category = "schema_missing"
        elif any(x in msg for x in ("does not exist", "undefined table", "42p01", "not found")):
            category = "table_not_found"
        elif any(x in msg for x in ("timeout", "timed out", "connection", "dns")):
            category = "connectivity_timeout"
        return OrderedDict([
            ("client_status", "CLIENT_RESOLVED"),
            ("read_only_connectivity_status", "READ_ONLY_CONNECTIVITY_BLOCKED"),
            ("selected_key_source", _t(credential_audit.get("supabase_key_source")) or "missing"),
            ("create_client_import_status", "ok" if resolution.get("supabase_package_available") else "unknown"),
            ("client_exception_class", None),
            ("client_exception_short_message", None),
            ("connectivity_exception_class", type(exc).__name__),
            ("connectivity_exception_short_message", _t(str(exc))[:160]),
            ("blocked_category", category),
            ("resolved_client_factory_source", _t(resolution.get("client_factory_source")) or "unavailable"),
            ("blocked_reason", f"READ_ONLY_PROBE_FAILED:{type(exc).__name__}"),
            ("table_probe", probe),
        ])

    return OrderedDict([
        ("client_status", "CLIENT_RESOLVED"),
        ("read_only_connectivity_status", "READ_ONLY_CONNECTIVITY_OK"),
        ("selected_key_source", _t(credential_audit.get("supabase_key_source")) or "missing"),
        ("create_client_import_status", "ok" if resolution.get("supabase_package_available") else "unknown"),
        ("client_exception_class", None),
        ("client_exception_short_message", None),
        ("connectivity_exception_class", None),
        ("connectivity_exception_short_message", None),
        ("blocked_category", None),
        ("resolved_client_factory_source", _t(resolution.get("client_factory_source")) or "unavailable"),
        ("blocked_reason", None),
        ("table_probe", probe),
    ])


def compare_dashboard_vs_operator_runtime_credentials(*, dashboard_runtime: Mapping[str, Any], operator_runtime: Mapping[str, Any]) -> OrderedDict[str, Any]:
    dk = bool(dashboard_runtime.get("supabase_key_present") or dashboard_runtime.get("credentials_present"))
    du = bool(dashboard_runtime.get("supabase_url_present") or dashboard_runtime.get("credentials_present"))
    ok = bool(operator_runtime.get("supabase_key_present") or operator_runtime.get("credentials_present"))
    ou = bool(operator_runtime.get("supabase_url_present") or operator_runtime.get("credentials_present"))
    return OrderedDict([
        ("dashboard_credentials_present", dk and du),
        ("operator_credentials_present", ok and ou),
        ("runtime_mismatch_detected", (dk and du) != (ok and ou)),
    ])


def build_d8_b2r2_connectivity_report_payload(*, credential_audit: Mapping[str, Any], connectivity_audit: Mapping[str, Any], dashboard_operator_comparison: Mapping[str, Any]) -> OrderedDict[str, Any]:
    if credential_audit.get("status") == "CREDENTIALS_MISSING":
        recommendation = "BLOCKED_MISSING_CREDENTIALS"
    elif credential_audit.get("status") == "CREDENTIALS_PARTIAL":
        recommendation = "BLOCKED_PARTIAL_CREDENTIALS"
    elif connectivity_audit.get("client_status") != "CLIENT_RESOLVED":
        recommendation = "BLOCKED_CLIENT_CONSTRUCTION"
    elif connectivity_audit.get("read_only_connectivity_status") != "READ_ONLY_CONNECTIVITY_OK":
        recommendation = "BLOCKED_READ_ONLY_CONNECTIVITY"
    else:
        recommendation = "READY_FOR_D8_B2R_RERUN"
    return OrderedDict([
        ("credential_audit", OrderedDict(credential_audit)),
        ("connectivity_audit", OrderedDict(connectivity_audit)),
        ("dashboard_vs_operator", OrderedDict(dashboard_operator_comparison)),
        ("recommendation", recommendation),
        ("governance_no_write_confirmed", True),
    ])
