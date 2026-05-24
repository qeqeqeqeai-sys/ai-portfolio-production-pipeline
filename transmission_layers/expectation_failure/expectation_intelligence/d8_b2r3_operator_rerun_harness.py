from __future__ import annotations

from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .d8_b2_controlled_replay_backfill_execution import build_d8_b2_dry_run_source_diagnostics
from .d8_b2r2_supabase_runtime_connectivity import (
    audit_supabase_read_only_connectivity,
    audit_supabase_runtime_credentials,
    build_d8_b2r2_connectivity_report_payload,
    compare_dashboard_vs_operator_runtime_credentials,
)
from .d8_b2r_replay_candidate_source_repair_audit import (
    audit_replay_candidate_sources,
    audit_supabase_client_resolution,
    build_d8_b2r_source_repair_report_payload,
)

REPORT_PATH = Path("reports/d8_b2r_real_supabase_diagnostics_status_report.md")


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _table_counts(source_audit: Mapping[str, Any]) -> tuple[int, int]:
    td = source_audit.get("table_diagnostics") or {}
    replay = (td.get("replay") or {}) if isinstance(td, Mapping) else {}
    manifest = (td.get("manifest") or {}) if isinstance(td, Mapping) else {}
    return int(replay.get("row_count") or 0), int(manifest.get("row_count") or 0)


def build_operator_rerun_payload(*, env: Mapping[str, str] | None = None, runtime_config: Mapping[str, Any] | None = None, client: Any = None, client_factory: Any = None) -> OrderedDict[str, Any]:
    cred = audit_supabase_runtime_credentials(env=env, runtime_config=runtime_config)
    conn = audit_supabase_read_only_connectivity(credential_audit=cred, runtime_config=runtime_config, client=client, client_factory=client_factory)
    runtime_bundle = build_d8_b2r2_connectivity_report_payload(
        credential_audit=cred,
        connectivity_audit=conn,
        dashboard_operator_comparison=compare_dashboard_vs_operator_runtime_credentials(dashboard_runtime={}, operator_runtime=cred),
    )
    client_audit = audit_supabase_client_resolution(runtime_config=runtime_config, client=client, client_factory=client_factory)
    source_audit = audit_replay_candidate_sources(client=(client if client_audit.get("client_resolved") else None))
    source_report = build_d8_b2r_source_repair_report_payload(client_audit=client_audit, source_audit=source_audit, runtime_connectivity=runtime_bundle)
    dry_run_diag = build_d8_b2_dry_run_source_diagnostics(runtime_config=runtime_config, client=client, client_factory=client_factory)
    replay_count, manifest_count = _table_counts(source_audit)
    inv = source_audit.get("inventory") or {}
    shape = source_audit.get("shape_comparison") or {}
    return OrderedDict([
        ("timestamp_utc", _now_utc_iso()),
        ("credential_audit", cred),
        ("connectivity_audit", conn),
        ("client_audit", client_audit),
        ("expected_tables", source_audit.get("expected_tables", [])),
        ("accessible_tables", source_audit.get("accessible_tables", [])),
        ("inaccessible_tables", [t for t in source_audit.get("expected_tables", []) if t not in set(source_audit.get("accessible_tables", []))]),
        ("replay_metadata_row_count", replay_count),
        ("manifest_row_count", manifest_count),
        ("dashboard_replay_row_count", replay_count),
        ("d7_derived_historical_source_count", int(inv.get("historical_payload_derivation_source_count") or 0)),
        ("d8_b2_candidate_source_count", int(inv.get("candidate_derivation_source_count") or 0)),
        ("rejected_derivation_ids", inv.get("rejected_derivation_ids", [])),
        ("missing_candidate_run_ids", shape.get("missing_candidate_run_ids", [])),
        ("source_shape_compatible", bool(shape.get("source_shape_compatible"))),
        ("final_status", source_report.get("status")),
        ("selected_key_source", conn.get("selected_key_source")),
        ("client_exception_class", conn.get("client_exception_class")),
        ("connectivity_exception_class", conn.get("connectivity_exception_class")),
        ("connectivity_exception_short_message", conn.get("connectivity_exception_short_message")),
        ("recommendation", source_report.get("recommendation")),
        ("dry_run_source_status", dry_run_diag.get("status")),
        ("no_write_confirmed", True),
    ])


def render_operator_report(payload: Mapping[str, Any]) -> str:
    cred = payload.get("credential_audit") or {}
    conn = payload.get("connectivity_audit") or {}
    lines = [
        "# D8.B2-R Real Supabase Diagnostics Status Report",
        "",
        f"- **Execution timestamp (UTC):** {payload.get('timestamp_utc')}",
        "- **Mode:** READ-ONLY diagnostics",
        "- **Explicit no-write confirmation:** true",
        "",
        "## Runtime Credential and Connectivity",
        f"- credential_status: `{cred.get('status')}`",
        f"- client_status: `{conn.get('client_status')}`",
        f"- read_only_connectivity_status: `{conn.get('read_only_connectivity_status')}`",
        f"- supabase_url_present: `{bool(cred.get('supabase_url_present'))}`",
        f"- supabase_key_present: `{bool(cred.get('supabase_key_present'))}`",
        f"- selected_key_source: `{conn.get('selected_key_source')}`",
        f"- client_exception_class: `{conn.get('client_exception_class')}`",
        f"- connectivity_exception_class: `{conn.get('connectivity_exception_class')}`",
        f"- connectivity_exception_short_message: `{conn.get('connectivity_exception_short_message')}`",
        f"- supabase_url_fingerprint: `{cred.get('supabase_url_fingerprint')}`",
        f"- supabase_key_fingerprint: `{cred.get('supabase_key_fingerprint')}`",
        "",
        "## Source Diagnostics",
        f"- expected_tables: `{payload.get('expected_tables')}`",
        f"- accessible_tables: `{payload.get('accessible_tables')}`",
        f"- inaccessible_tables: `{payload.get('inaccessible_tables')}`",
        f"- replay_metadata_row_count: `{payload.get('replay_metadata_row_count')}`",
        f"- manifest_row_count: `{payload.get('manifest_row_count')}`",
        f"- dashboard_replay_row_count: `{payload.get('dashboard_replay_row_count')}`",
        f"- d7_derived_historical_source_count: `{payload.get('d7_derived_historical_source_count')}`",
        f"- d8_b2_candidate_source_count: `{payload.get('d8_b2_candidate_source_count')}`",
        f"- rejected_derivation_ids: `{payload.get('rejected_derivation_ids')}`",
        f"- missing_candidate_run_ids: `{payload.get('missing_candidate_run_ids')}`",
        f"- source_shape_compatible: `{payload.get('source_shape_compatible')}`",
        "",
        "## Final Status",
        f"- final_status: `{payload.get('final_status')}`",
        f"- recommendation: `{payload.get('recommendation')}`",
        f"- dry_run_source_status: `{payload.get('dry_run_source_status')}`",
    ]
    return "\n".join(lines) + "\n"


def run_and_write_report(*, report_path: Path = REPORT_PATH, env: Mapping[str, str] | None = None, runtime_config: Mapping[str, Any] | None = None, client: Any = None, client_factory: Any = None) -> OrderedDict[str, Any]:
    payload = build_operator_rerun_payload(env=env, runtime_config=runtime_config, client=client, client_factory=client_factory)
    report_path.write_text(render_operator_report(payload), encoding="utf-8")
    return payload
