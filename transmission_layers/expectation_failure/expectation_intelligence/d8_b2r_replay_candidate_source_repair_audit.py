from __future__ import annotations

from collections import OrderedDict
from typing import Any, Mapping

from .d8_b2r2_supabase_runtime_connectivity import (
    audit_supabase_read_only_connectivity,
    audit_supabase_runtime_credentials,
    build_d8_b2r2_connectivity_report_payload,
    compare_dashboard_vs_operator_runtime_credentials,
)

from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o7_streamlit_supabase_runtime import (
    resolve_streamlit_supabase_client,
)
from transmission_layers.expectation_failure.dashboard_operationalization.d7_streamlit_dashboard_viewer import (
    D7_PHYSICAL_COLUMNS_BY_TABLE,
    build_d7_historical_runs_from_integrity,
)

EXPECTED_TABLES = (
    "dashboard_replay_metadata_records",
    "dashboard_export_manifests",
)
REQUIRED_CANDIDATE_FIELDS = ("run_id", "run_timestamp", "payload_checksum", "source_trace", "payload_reference")


def _as_list(v: Any) -> list[Any]:
    return list(v) if isinstance(v, list) else []


def _as_text(v: Any) -> str:
    return str(v).strip() if v is not None else ""


def audit_supabase_client_resolution(*, runtime_config: Mapping[str, Any] | None = None, client: Any = None, client_factory: Any = None) -> OrderedDict[str, Any]:
    config = dict(runtime_config or {})
    resolved = resolve_streamlit_supabase_client(config, client=client, client_factory=client_factory)
    return OrderedDict([
        ("client_resolved", bool(resolved.get("client_resolved"))),
        ("client_factory_source", _as_text(resolved.get("client_factory_source")) or "unavailable"),
        ("client_error_type", resolved.get("client_error_type")),
        ("credential_presence_flags", OrderedDict([
            ("credentials_present", bool(config.get("credentials_present"))),
            ("supabase_url_present", bool(config.get("supabase_url"))),
            ("supabase_key_present", bool(config.get("supabase_key"))),
        ])),
    ])


def _safe_table_rows(client: Any, table: str, columns: list[str]) -> OrderedDict[str, Any]:
    if client is None:
        return OrderedDict([("table", table), ("status", "unreachable"), ("row_count", 0), ("rows", []), ("error", "client_not_resolved")])
    try:
        result = client.table(table).select(",".join(columns)).limit(500).execute()
        rows = [r for r in _as_list(getattr(result, "data", [])) if isinstance(r, Mapping)]
        return OrderedDict([("table", table), ("status", "ok" if rows else "empty"), ("row_count", len(rows)), ("rows", rows), ("error", None)])
    except Exception as exc:
        return OrderedDict([("table", table), ("status", "error"), ("row_count", 0), ("rows", []), ("error", f"{type(exc).__name__}:{str(exc)[:120]}")])


def adapt_history_row_to_candidate(row: Mapping[str, Any]) -> OrderedDict[str, Any] | None:
    run_id = _as_text(row.get("run_id") or row.get("replay_id") or row.get("record_id"))
    run_timestamp = _as_text(row.get("run_timestamp") or row.get("timestamp") or row.get("created_at"))
    payload_checksum = _as_text(row.get("payload_checksum") or row.get("source_payload_checksum") or row.get("checksum_lineage"))
    source_trace = _as_text(row.get("source_trace") or row.get("lineage_source") or "persisted_replay")
    payload_reference = _as_text(row.get("payload_reference") or row.get("record_id") or row.get("replay_id"))
    candidate = OrderedDict([
        ("run_id", run_id),
        ("run_timestamp", run_timestamp),
        ("payload_checksum", payload_checksum),
        ("source_trace", source_trace),
        ("payload_reference", payload_reference),
    ])
    if all(_as_text(candidate.get(k)) for k in REQUIRED_CANDIDATE_FIELDS):
        return candidate
    return None


def build_replay_candidate_source_inventory(*, replay_rows: list[Mapping[str, Any]], historical_runs_payloads: list[Mapping[str, Any]]) -> OrderedDict[str, Any]:
    candidates = []
    rejected = []
    for row in _as_list(historical_runs_payloads):
        if not isinstance(row, Mapping):
            continue
        cand = adapt_history_row_to_candidate(row)
        if cand is None:
            rejected.append(_as_text(row.get("run_id") or row.get("record_id") or "missing_id"))
        else:
            candidates.append(cand)
    return OrderedDict([
        ("replay_metadata_row_count", len([r for r in _as_list(replay_rows) if isinstance(r, Mapping)])),
        ("historical_payload_derivation_source_count", len([r for r in _as_list(historical_runs_payloads) if isinstance(r, Mapping)])),
        ("candidate_derivation_source_count", len(candidates)),
        ("rejected_derivation_ids", sorted(set(rejected))),
        ("candidates", sorted(candidates, key=lambda x: (_as_text(x.get("run_timestamp")), _as_text(x.get("run_id"))))),
    ])


def compare_d7_history_sources_to_d8b2_candidate_sources(*, historical_runs_payloads: list[Mapping[str, Any]], candidates: list[Mapping[str, Any]]) -> OrderedDict[str, Any]:
    history_ids = {_as_text(r.get("run_id")) for r in _as_list(historical_runs_payloads) if isinstance(r, Mapping)}
    candidate_ids = {_as_text(c.get("run_id")) for c in _as_list(candidates) if isinstance(c, Mapping)}
    missing = sorted(x for x in history_ids if x and x not in candidate_ids)
    return OrderedDict([
        ("history_run_count", len([x for x in history_ids if x])),
        ("candidate_run_count", len([x for x in candidate_ids if x])),
        ("missing_candidate_run_ids", missing),
        ("source_shape_compatible", not missing),
    ])


def audit_replay_candidate_sources(*, client: Any, findings: list[Mapping[str, Any]] | None = None, narratives: list[Mapping[str, Any]] | None = None, evidence_maps: list[Mapping[str, Any]] | None = None) -> OrderedDict[str, Any]:
    replay_payload = _safe_table_rows(client, "dashboard_replay_metadata_records", D7_PHYSICAL_COLUMNS_BY_TABLE["dashboard_replay_metadata_records"])
    manifest_payload = _safe_table_rows(client, "dashboard_export_manifests", D7_PHYSICAL_COLUMNS_BY_TABLE["dashboard_export_manifests"])
    history = build_d7_historical_runs_from_integrity(
        replay_rows=_as_list(replay_payload.get("rows")), findings=_as_list(findings), narratives=_as_list(narratives), evidence_maps=_as_list(evidence_maps)
    )
    inv = build_replay_candidate_source_inventory(replay_rows=_as_list(replay_payload.get("rows")), historical_runs_payloads=history)
    cmp = compare_d7_history_sources_to_d8b2_candidate_sources(historical_runs_payloads=history, candidates=_as_list(inv.get("candidates")))
    return OrderedDict([
        ("expected_tables", list(EXPECTED_TABLES)),
        ("accessible_tables", [x["table"] for x in (replay_payload, manifest_payload) if x.get("status") in {"ok", "empty"}]),
        ("table_diagnostics", OrderedDict([("replay", replay_payload), ("manifest", manifest_payload)])),
        ("inventory", inv),
        ("shape_comparison", cmp),
    ])


def build_d8_b2r_source_repair_report_payload(*, client_audit: Mapping[str, Any], source_audit: Mapping[str, Any], runtime_connectivity: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    runtime = dict(runtime_connectivity or {})
    if runtime:
        rec = runtime.get("recommendation")
        if rec == "BLOCKED_MISSING_CREDENTIALS":
            status = "SOURCE_BLOCKED_CREDENTIALS_MISSING"
            recommendation = rec
        elif rec == "BLOCKED_PARTIAL_CREDENTIALS":
            status = "SOURCE_BLOCKED_CREDENTIALS_PARTIAL"
            recommendation = rec
        elif rec == "BLOCKED_CLIENT_CONSTRUCTION":
            status = "SOURCE_BLOCKED_CLIENT_UNRESOLVED"
            recommendation = rec
        elif rec == "BLOCKED_READ_ONLY_CONNECTIVITY":
            status = "SOURCE_BLOCKED_READ_ONLY_CONNECTIVITY"
            recommendation = rec
        elif rec == "READY_FOR_D8_B2R_RERUN":
            status = "SOURCE_READY"
            recommendation = rec
        else:
            status = "SOURCE_BLOCKED_CLIENT_UNRESOLVED"
            recommendation = "BLOCKED_CLIENT_CONFIGURATION"
    elif not client_audit.get("client_resolved"):
        status = "SOURCE_BLOCKED_CLIENT_UNRESOLVED"
        recommendation = "BLOCKED_CLIENT_CONFIGURATION"
    elif not source_audit.get("accessible_tables"):
        status = "SOURCE_BLOCKED_TABLE_MISMATCH"
        recommendation = "BLOCKED_SCHEMA_OR_SHAPE_MISMATCH"
    elif int(((source_audit.get("inventory") or {}).get("replay_metadata_row_count") or 0)) == 0:
        status = "SOURCE_EMPTY_BUT_VALID"
        recommendation = "BLOCKED_EMPTY_SOURCE"
    elif not bool(((source_audit.get("shape_comparison") or {}).get("source_shape_compatible"))):
        status = "SOURCE_BLOCKED_SHAPE_MISMATCH"
        recommendation = "BLOCKED_SCHEMA_OR_SHAPE_MISMATCH"
    elif int(((source_audit.get("inventory") or {}).get("candidate_derivation_source_count") or 0)) == 0:
        status = "SOURCE_BLOCKED_NO_CANDIDATES"
        recommendation = "BLOCKED_NO_VALID_CANDIDATES"
    else:
        status = "SOURCE_READY"
        recommendation = "READY_FOR_D8_B2_DRY_RUN_RETRY"
    return OrderedDict([
        ("status", status),
        ("recommendation", recommendation),
        ("client_audit", OrderedDict(client_audit)),
        ("source_audit", OrderedDict(source_audit)),
    ])


def build_d8_b2r2_runtime_connectivity_bundle(*, runtime_config: Mapping[str, Any] | None = None, client: Any = None, client_factory: Any = None, dashboard_runtime: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    credential_audit = audit_supabase_runtime_credentials(runtime_config=runtime_config)
    connectivity_audit = audit_supabase_read_only_connectivity(
        credential_audit=credential_audit, runtime_config=runtime_config, client=client, client_factory=client_factory
    )
    comparison = compare_dashboard_vs_operator_runtime_credentials(
        dashboard_runtime=dict(dashboard_runtime or {}), operator_runtime=credential_audit
    )
    return build_d8_b2r2_connectivity_report_payload(
        credential_audit=credential_audit, connectivity_audit=connectivity_audit, dashboard_operator_comparison=comparison
    )
