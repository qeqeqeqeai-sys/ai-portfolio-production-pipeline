"""Dashboard O7 Streamlit runtime boundary for deterministic Supabase read-only loading."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from typing import Any, Mapping
import os

SCHEMA_VERSION = "dashboard_o7_streamlit_supabase_runtime_v1"
MODULE_VERSION = "1.1.0"
DEFAULT_CACHE_TTL_SECONDS = 120


_O4_REQUIRED_SECTIONS = (
    "entity_facts",
    "subsector_facts",
    "alert_facts",
    "replay_facts",
    "benchmark_facts",
    "evidence_facts",
    "certification_metadata",
)


_EXPECTED_TABLES = (
    "dashboard_entity_facts",
    "dashboard_subsector_facts",
    "dashboard_alert_facts",
    "dashboard_replay_facts",
    "dashboard_benchmark_facts",
    "dashboard_evidence_facts",
    "dashboard_certification_reports",
    "dashboard_run_manifests",
)


def _safe_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def build_streamlit_supabase_runtime_config(*, supabase_url: str | None = None, supabase_key: str | None = None, run_id: str | None = None, as_of_date: str | None = None, cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS) -> OrderedDict:
    runtime_url = _safe_text(supabase_url)
    runtime_key = _safe_text(supabase_key)
    url_source = "arg" if runtime_url else ("env:SUPABASE_URL" if _safe_text(os.getenv("SUPABASE_URL")) else "missing")
    key_source = "arg" if runtime_key else ("env:SUPABASE_ANON_KEY" if _safe_text(os.getenv("SUPABASE_ANON_KEY")) else ("env:SUPABASE_KEY" if _safe_text(os.getenv("SUPABASE_KEY")) else "missing"))
    cfg = OrderedDict([
        ("supabase_url", runtime_url or _safe_text(os.getenv("SUPABASE_URL"))),
        ("supabase_key", runtime_key or _safe_text(os.getenv("SUPABASE_ANON_KEY")) or _safe_text(os.getenv("SUPABASE_KEY"))),
        ("run_id", _safe_text(run_id)),
        ("as_of_date", _safe_text(as_of_date)),
        ("supabase_url_source", url_source),
        ("supabase_key_source", key_source),
        ("github_actions_supabase_url", _safe_text(os.getenv("GITHUB_ACTIONS_SUPABASE_URL"))),
    ])
    ttl = int(cache_ttl_seconds) if isinstance(cache_ttl_seconds, int) else DEFAULT_CACHE_TTL_SECONDS
    cfg["cache_ttl_seconds"] = 30 if ttl < 30 else min(ttl, 3600)
    cfg["credentials_present"] = bool(cfg["supabase_url"] and cfg["supabase_key"])
    cfg["refresh_policy"] = "manual_or_rerun_only"
    cfg["background_polling_enabled"] = False
    return cfg


def _redact_and_truncate_error(value: Any, *, max_len: int = 200) -> str | None:
    if value is None:
        return None
    txt = str(value).strip()
    if not txt:
        return None
    redacted = txt
    for token in ("supabase_key", "SUPABASE_KEY", "SUPABASE_ANON_KEY", "apikey", "api_key", "token", "secret", "password"):
        redacted = redacted.replace(token, "[REDACTED]")
    for marker in ("sk-", "sbp_", "eyJ"):
        if marker in redacted:
            redacted = redacted.replace(marker, "[REDACTED]-")
    return redacted[:max_len]


def resolve_streamlit_supabase_client(runtime_config: Mapping[str, Any], *, client: Any | None = None, client_factory: Any | None = None) -> OrderedDict:
    credentials_present = bool(runtime_config.get("credentials_present"))
    if client is not None:
        return OrderedDict([
            ("client", client),
            ("client_resolved", True),
            ("client_error_type", None),
            ("client_error_message_short", None),
            ("client_factory_source", "injected_client"),
            ("supabase_package_available", True),
            ("credentials_present", credentials_present),
        ])

    package_available = False
    resolved_factory = client_factory
    factory_source = "injected_factory" if client_factory is not None else "unavailable"
    if resolved_factory is None and credentials_present:
        try:
            from supabase import create_client as package_factory  # type: ignore

            resolved_factory = package_factory
            package_available = True
            factory_source = "supabase_package"
        except Exception as exc:
            return OrderedDict([
                ("client", None),
                ("client_resolved", False),
                ("client_error_type", type(exc).__name__),
                ("client_error_message_short", _redact_and_truncate_error(str(exc))),
                ("client_factory_source", "unavailable"),
                ("supabase_package_available", False),
                ("credentials_present", credentials_present),
            ])

    if not credentials_present:
        return OrderedDict([
            ("client", None),
            ("client_resolved", False),
            ("client_error_type", "CredentialsMissing"),
            ("client_error_message_short", "Supabase runtime credentials are missing."),
            ("client_factory_source", "unavailable" if client_factory is None else "injected_factory"),
            ("supabase_package_available", package_available),
            ("credentials_present", credentials_present),
        ])

    if resolved_factory is None:
        return OrderedDict([
            ("client", None),
            ("client_resolved", False),
            ("client_error_type", "ClientFactoryUnavailable"),
            ("client_error_message_short", "No Supabase client factory is available."),
            ("client_factory_source", factory_source),
            ("supabase_package_available", package_available),
            ("credentials_present", credentials_present),
        ])

    try:
        resolved_client = resolved_factory(runtime_config.get("supabase_url"), runtime_config.get("supabase_key"))
        return OrderedDict([
            ("client", resolved_client),
            ("client_resolved", resolved_client is not None),
            ("client_error_type", None if resolved_client is not None else "ClientFactoryReturnedNone"),
            ("client_error_message_short", None if resolved_client is not None else "Supabase client factory returned None."),
            ("client_factory_source", factory_source),
            ("supabase_package_available", package_available),
            ("credentials_present", credentials_present),
        ])
    except Exception as exc:
        return OrderedDict([
            ("client", None),
            ("client_resolved", False),
            ("client_error_type", type(exc).__name__),
            ("client_error_message_short", _redact_and_truncate_error(str(exc))),
            ("client_factory_source", factory_source),
            ("supabase_package_available", package_available),
            ("credentials_present", credentials_present),
        ])


def _section_status(snapshot: Mapping[str, Any], section: str) -> str:
    part = snapshot.get(section)
    if isinstance(part, Mapping):
        return str(part.get("status", "degraded"))
    return "degraded"


def _build_section_read_diagnostics(snapshot: Mapping[str, Any] | None) -> list[OrderedDict]:
    section_to_table = OrderedDict([
        ("entity_facts", "dashboard_entity_facts"),
        ("subsector_facts", "dashboard_subsector_facts"),
        ("alert_facts", "dashboard_alert_facts"),
        ("replay_facts", "dashboard_replay_facts"),
        ("benchmark_facts", "dashboard_benchmark_facts"),
        ("evidence_facts", "dashboard_evidence_facts"),
        ("certification_metadata", "dashboard_certification_reports"),
    ])
    out=[]
    snap = snapshot or {}
    col_inventory = snap.get("column_inventory") if isinstance(snap, Mapping) else {}
    filter_map = snap.get("section_filter_map") if isinstance(snap, Mapping) else {}
    for section, table in section_to_table.items():
        part = snap.get(section) if isinstance(snap, Mapping) else None
        status = _section_status(snap, section)
        rows = part.get("rows", []) if isinstance(part, Mapping) else []
        row_count = part.get("row_count") if isinstance(part, Mapping) else None
        row_count = len(rows) if row_count is None and isinstance(rows, list) else row_count
        required = list((col_inventory or {}).get(table, []))
        sample_keys = sorted(list(rows[0].keys()))[:30] if rows and isinstance(rows[0], Mapping) else []
        missing_columns = [c for c in required if c not in sample_keys] if sample_keys else ([] if status in {"empty","missing","permission_denied","query_failed"} else required)
        required_present = None if status in {"missing","permission_denied","query_failed"} else (len(missing_columns)==0)
        error = part.get("error") if isinstance(part, Mapping) else None
        error_type = None
        error_message_short = None
        if error:
            if ":" in str(error):
                error_type, msg = str(error).split(":",1)
                error_type=error_type.strip()
                error_message_short=msg.strip()[:200]
            else:
                error_message_short=str(error)[:200]
        out.append(OrderedDict([("table_name", table), ("section_name", section), ("status", status), ("row_count", row_count), ("required_columns_present", required_present), ("missing_columns", missing_columns), ("error_type", error_type), ("error_message_short", _redact_and_truncate_error(error_message_short)), ("filter_applied", (filter_map or {}).get(section, "none")), ("sample_row_keys", sample_keys)]))
    return out


def _health_interpretation(section_read_diagnostics: list[Mapping[str, Any]]) -> str:
    statuses=[str(x.get("status")) for x in section_read_diagnostics]
    if statuses and all(s=="ok" for s in statuses):
        return "supabase_snapshot_healthy"
    if statuses and all(s=="empty" for s in statuses):
        return "tables_exist_but_empty_or_filters_exclude_rows"
    if any(s=="missing" for s in statuses):
        return "dashboard_tables_missing"
    if any(s=="permission_denied" for s in statuses):
        return "rls_or_permission_denied"
    if any(s=="schema_mismatch" for s in statuses):
        return "dashboard_schema_mismatch"
    if any(s=="query_failed" for s in statuses):
        return "supabase_query_failed"
    if any(s!="ok" for s in statuses):
        return "mixed_section_degradation"
    return "mixed_section_degradation"


def resolve_streamlit_supabase_mode(runtime_config: Mapping[str, Any], *, snapshot: Mapping[str, Any] | None = None) -> str:
    if not runtime_config.get("credentials_present"):
        return "fallback_demo_mode"
    if snapshot is None:
        return "read_only_supabase_mode"
    degraded = any(_section_status(snapshot, section) != "ok" for section in _O4_REQUIRED_SECTIONS)
    return "degraded_data_loading_mode" if degraded else "read_only_supabase_mode"


def _as_section_rows(snapshot: Mapping[str, Any], section: str) -> list[dict[str, Any]]:
    part = snapshot.get(section)
    rows = part.get("rows", []) if isinstance(part, Mapping) else []
    return [dict(row) for row in rows if isinstance(row, Mapping)]


def _build_runtime_diagnostics(*, runtime_config: Mapping[str, Any], snapshot: Mapping[str, Any] | None, payload_source: str, normalization_status: str, error: str | None, runtime_mode: str, client_resolved: bool, client_error_type: str | None = None, client_error_message_short: str | None = None, client_factory_source: str = "unavailable", supabase_package_available: bool = False) -> OrderedDict:
    section_statuses = OrderedDict((section, _section_status(snapshot or {}, section)) for section in _O4_REQUIRED_SECTIONS)
    degraded_sections = [section for section, status in section_statuses.items() if status != "ok"]
    error_type = None
    error_message_short = None
    if error:
        if ":" in error:
            error_type, msg = error.split(":", 1)
            error_type = error_type.strip() or None
            error_message_short = msg.strip()[:200] or None
        else:
            error_message_short = str(error).strip()[:200] or None
    section_read_diagnostics = _build_section_read_diagnostics(snapshot)
    missing_tables = [x["table_name"] for x in section_read_diagnostics if x["status"] == "missing"]
    empty_sections = [x["section_name"] for x in section_read_diagnostics if x["status"] == "empty"]
    permission_denied_tables = [x["table_name"] for x in section_read_diagnostics if x["status"] == "permission_denied"]
    schema_mismatch_tables = [x["table_name"] for x in section_read_diagnostics if x["status"] == "schema_mismatch"]
    query_failed_tables = [x["table_name"] for x in section_read_diagnostics if x["status"] == "query_failed"]
    health_interpretation = _health_interpretation(section_read_diagnostics)
    return OrderedDict([
        ("credentials_present", bool(runtime_config.get("credentials_present"))),
        ("client_resolved", bool(client_resolved)),
        ("snapshot_loaded", snapshot is not None and bool(client_resolved)),
        ("snapshot_section_statuses", section_statuses),
        ("degraded_sections", degraded_sections),
        ("normalization_status", normalization_status),
        ("payload_source", payload_source),
        ("error_type", error_type),
        ("error_message_short", error_message_short),
        ("client_error_type", client_error_type),
        ("client_error_message_short", client_error_message_short),
        ("client_factory_source", client_factory_source),
        ("supabase_package_available", bool(supabase_package_available)),
        ("expected_tables", list(_EXPECTED_TABLES)),
        ("runtime_mode", runtime_mode),
        ("section_read_diagnostics", section_read_diagnostics),
        ("empty_sections", empty_sections),
        ("missing_tables", missing_tables),
        ("permission_denied_tables", permission_denied_tables),
        ("schema_mismatch_tables", schema_mismatch_tables),
        ("query_failed_tables", query_failed_tables),
        ("health_interpretation", health_interpretation),
    ])


def _attach_runtime_diagnostics(payload: Mapping[str, Any], diagnostics: Mapping[str, Any]) -> OrderedDict:
    payload_with_diagnostics = OrderedDict(deepcopy(dict(payload or {})))
    payload_with_diagnostics["runtime_diagnostics"] = OrderedDict(deepcopy(dict(diagnostics or {})))
    return payload_with_diagnostics


def build_dashboard_payload_from_supabase_snapshot(snapshot: Mapping[str, Any], fallback_payload: Mapping[str, Any] | None = None) -> OrderedDict:
    snap = deepcopy(dict(snapshot or {}))
    rows_by_section = {section: _as_section_rows(snap, section) for section in _O4_REQUIRED_SECTIONS}
    if any(_section_status(snap, section) != "ok" for section in _O4_REQUIRED_SECTIONS):
        raise ValueError("snapshot_sections_degraded_or_unavailable")

    report_row = rows_by_section["certification_metadata"][0] if rows_by_section["certification_metadata"] else {}
    export_manifest_checksum = report_row.get("export_manifest_checksum")
    report_metadata = OrderedDict([
        ("run_id", report_row.get("run_id")),
        ("run_date_sgt", report_row.get("run_date_sgt")),
        ("certification_status", report_row.get("certification_status")),
        ("report_type", report_row.get("report_type")),
        ("export_manifest_checksum", export_manifest_checksum),
    ])
    export_manifest = OrderedDict([("checksum", export_manifest_checksum)])

    return OrderedDict([
        ("dashboard_entity_facts", rows_by_section["entity_facts"]),
        ("dashboard_subsector_facts", rows_by_section["subsector_facts"]),
        ("dashboard_alert_facts", rows_by_section["alert_facts"]),
        ("dashboard_replay_facts", rows_by_section["replay_facts"]),
        ("dashboard_benchmark_facts", rows_by_section["benchmark_facts"]),
        ("dashboard_evidence_facts", rows_by_section["evidence_facts"]),
        ("dashboard_report_metadata", report_metadata),
        ("dashboard_export_manifest", export_manifest),
    ])


def load_streamlit_dashboard_snapshot(*, runtime_config: Mapping[str, Any], fallback_payload: Mapping[str, Any], client: Any | None = None, client_factory: Any | None = None) -> OrderedDict:
    config = deepcopy(dict(runtime_config))
    payload = deepcopy(dict(fallback_payload))
    mode = resolve_streamlit_supabase_mode(config)
    if mode == "fallback_demo_mode":
        diagnostics = _build_runtime_diagnostics(
            runtime_config=config,
            snapshot=None,
            payload_source="fallback_payload",
            normalization_status="not_applicable",
            error=None,
            runtime_mode=mode,
            client_resolved=False,
        )
        return OrderedDict([
            ("mode", mode), ("snapshot", None), ("payload", _attach_runtime_diagnostics(payload, diagnostics)), ("payload_source", "fallback_payload"),
            ("status", "ok"), ("normalization_status", "not_applicable"), ("error", None),
            ("runtime_diagnostics", diagnostics),
        ])

    snapshot: Mapping[str, Any]
    try:
        from .dashboard_o6_supabase_read_adapter import build_dashboard_supabase_snapshot

        client_resolution = resolve_streamlit_supabase_client(config, client=client, client_factory=client_factory)
        client_resolved = bool(client_resolution["client_resolved"])
        if not client_resolved:
            diagnostics = _build_runtime_diagnostics(
                runtime_config=config,
                snapshot=None,
                payload_source="fallback_payload",
                normalization_status="client_unresolved",
                error=None,
                runtime_mode="degraded_data_loading_mode",
                client_resolved=False,
                client_error_type=client_resolution.get("client_error_type"),
                client_error_message_short=client_resolution.get("client_error_message_short"),
                client_factory_source=str(client_resolution.get("client_factory_source", "unavailable")),
                supabase_package_available=bool(client_resolution.get("supabase_package_available", False)),
            )
            return OrderedDict([
                ("mode", "degraded_data_loading_mode"), ("snapshot", None), ("payload", _attach_runtime_diagnostics(payload, diagnostics)), ("payload_source", "fallback_payload"),
                ("status", "ok"), ("normalization_status", "client_unresolved"), ("error", None),
                ("runtime_diagnostics", diagnostics),
            ])
        supabase_client = client_resolution["client"]
        resolved_factory_source = str(client_resolution.get("client_factory_source", "unavailable"))
        resolved_package_available = bool(client_resolution.get("supabase_package_available", False))
        snapshot = build_dashboard_supabase_snapshot(supabase_client, run_id=config.get("run_id"), as_of_date=config.get("as_of_date"))
        mode = resolve_streamlit_supabase_mode(config, snapshot=snapshot)
    except Exception as exc:
        snapshot = OrderedDict([("error", f"{type(exc).__name__}: {str(exc)[:200]}")])
        error_text = snapshot.get("error")
        diagnostics = _build_runtime_diagnostics(
            runtime_config=config,
            snapshot=snapshot,
            payload_source="fallback_payload",
            normalization_status="snapshot_read_failed",
            error=error_text,
            runtime_mode="degraded_data_loading_mode",
            client_resolved=False,
        )
        return OrderedDict([
            ("mode", "degraded_data_loading_mode"), ("snapshot", snapshot), ("payload", _attach_runtime_diagnostics(payload, diagnostics)), ("payload_source", "fallback_payload"),
            ("status", "ok"), ("normalization_status", "snapshot_read_failed"), ("error", error_text),
            ("runtime_diagnostics", diagnostics),
        ])

    if mode != "read_only_supabase_mode":
        diagnostics = _build_runtime_diagnostics(
            runtime_config=config,
            snapshot=snapshot,
            payload_source="fallback_payload",
            normalization_status="snapshot_degraded",
            error=None,
            runtime_mode=mode,
            client_resolved=client_resolved,
            client_factory_source=resolved_factory_source,
            supabase_package_available=resolved_package_available,
        )
        return OrderedDict([
            ("mode", mode), ("snapshot", snapshot), ("payload", _attach_runtime_diagnostics(payload, diagnostics)), ("payload_source", "fallback_payload"),
            ("status", "ok"), ("normalization_status", "snapshot_degraded"), ("error", None),
            ("runtime_diagnostics", diagnostics),
        ])

    try:
        normalized_payload = build_dashboard_payload_from_supabase_snapshot(snapshot, fallback_payload=payload)
        diagnostics = _build_runtime_diagnostics(
            runtime_config=config,
            snapshot=snapshot,
            payload_source="supabase_snapshot",
            normalization_status="ok",
            error=None,
            runtime_mode=mode,
            client_resolved=client_resolved,
            client_factory_source=resolved_factory_source,
            supabase_package_available=resolved_package_available,
        )
        return OrderedDict([
            ("mode", mode), ("snapshot", snapshot), ("payload", _attach_runtime_diagnostics(normalized_payload, diagnostics)), ("payload_source", "supabase_snapshot"),
            ("status", "ok"), ("normalization_status", "ok"), ("error", None),
            ("runtime_diagnostics", diagnostics),
        ])
    except Exception as exc:
        error_text = f"{type(exc).__name__}: {str(exc)[:200]}"
        diagnostics = _build_runtime_diagnostics(
            runtime_config=config,
            snapshot=snapshot,
            payload_source="fallback_payload",
            normalization_status="failed",
            error=error_text,
            runtime_mode="degraded_data_loading_mode",
            client_resolved=client_resolved,
            client_factory_source=resolved_factory_source,
            supabase_package_available=resolved_package_available,
        )
        return OrderedDict([
            ("mode", "degraded_data_loading_mode"), ("snapshot", snapshot), ("payload", _attach_runtime_diagnostics(payload, diagnostics)), ("payload_source", "fallback_payload"),
            ("status", "ok"), ("normalization_status", "failed"), ("error", error_text),
            ("runtime_diagnostics", diagnostics),
        ])


def build_dashboard_o7_runtime_report_payload() -> OrderedDict:
    return OrderedDict([
        ("schema_version", SCHEMA_VERSION),
        ("module_version", MODULE_VERSION),
        ("objective", "Runtime-only Streamlit Supabase client boundary with deterministic read-only fallback/degraded behavior."),
        ("runtime_boundary", "Client creation/resolution only at Streamlit runtime boundary; O6 remains injected-client-only."),
        ("read_only_guarantees", ["no_writes", "no_inserts_updates_deletes", "no_rpc", "no_raw_sql", "bounded_table_access_via_o6"]),
        ("refresh_model", OrderedDict([("manual_or_rerun_only", True), ("background_polling", False), ("cache_ttl_bounds_seconds", [30, 3600])])),
        ("modes", ["read_only_supabase_mode", "fallback_demo_mode", "degraded_data_loading_mode"]),
        ("deterministic_guarantees", ["immutable_input_safe", "deterministic_mode_resolution", "deterministic_fallback_payload_passthrough", "additive_only"]),
    ])


__all__ = [
    "build_streamlit_supabase_runtime_config",
    "resolve_streamlit_supabase_mode",
    "build_dashboard_payload_from_supabase_snapshot",
    "load_streamlit_dashboard_snapshot",
    "build_dashboard_o7_runtime_report_payload",
]
