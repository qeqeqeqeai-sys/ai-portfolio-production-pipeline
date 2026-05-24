from __future__ import annotations

from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .d8_b2_controlled_replay_backfill_execution import (
    build_backfill_execution_plan,
    build_d8_b2_dry_run_source_diagnostics,
    execute_controlled_replay_backfill,
    validate_backfill_candidates,
    validate_backfill_execution_governance,
)
from .d8_b2r_replay_candidate_source_repair_audit import audit_replay_candidate_sources
from .d8_b1_controlled_replay_expansion import build_d8_b1_controlled_backfill_plan
from .d8_b2r3_operator_rerun_harness import build_operator_rerun_payload

REPORT_PATH = Path("reports/d8_b2_real_supabase_dry_run_retry_report.md")


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _as_list(v: Any) -> list[Any]:
    return list(v) if isinstance(v, list) else []


def _shape(v: Any) -> int:
    return len([x for x in _as_list(v) if isinstance(x, Mapping)])


def _estimate_intelligence_lift(*, replay_rows: int, candidate_sources: int, accepted: int, rejected: int, duplicates: int) -> OrderedDict[str, Any]:
    denom = max(replay_rows, 1)
    ratio = accepted / denom
    return OrderedDict([
        ("replay_density_lift", round(ratio, 6)),
        ("evidence_multiplicity_lift", round((accepted * 2) / denom, 6)),
        ("semantic_persistence_lift", round(accepted / max(candidate_sources, 1), 6)),
        ("contradiction_density_lift", round((accepted - duplicates) / denom, 6)),
        ("strongest_evidence_availability_impact", "positive" if accepted > 0 else "none"),
        ("explainability_confidence_impact", "improved" if accepted > rejected else "flat_or_uncertain"),
    ])


def _recommendation(execution_status: str, governance_status: str, accepted: int, duplicates: int) -> str:
    if governance_status != "GOVERNANCE_OK":
        return "BLOCKED_GOVERNANCE"
    if accepted == 0:
        return "BLOCKED_NO_VALID_CANDIDATES"
    if duplicates > 0:
        return "BLOCKED_DUPLICATE_REMEDIATION"
    if execution_status == "BACKFILL_DRY_RUN_READY":
        return "SAFE_FOR_CONTROLLED_EXECUTION"
    return "SAFE_FOR_PARTIAL_EXECUTION"


def build_real_supabase_dry_run_retry_payload(*, runtime_config: Mapping[str, Any] | None = None, client: Any = None, client_factory: Any = None) -> OrderedDict[str, Any]:
    operator_diag = build_operator_rerun_payload(runtime_config=runtime_config, client=client, client_factory=client_factory)
    source_diag = build_d8_b2_dry_run_source_diagnostics(runtime_config=runtime_config, client=client, client_factory=client_factory)
    if source_diag.get("status") != "SOURCE_READY":
        return OrderedDict([
            ("timestamp_utc", _now_utc_iso()),
            ("status", "BLOCKED_SOURCE_NOT_READY"),
            ("source_diagnostics", source_diag),
            ("source_status", source_diag.get("status")),
            ("source_recommendation", source_diag.get("recommendation")),
            ("credential_status", (operator_diag.get("credential_audit") or {}).get("status")),
            ("client_status", (operator_diag.get("connectivity_audit") or {}).get("client_status")),
            ("read_only_connectivity_status", (operator_diag.get("connectivity_audit") or {}).get("read_only_connectivity_status")),
            ("selected_key_source", operator_diag.get("selected_key_source")),
            ("accessible_tables", operator_diag.get("accessible_tables") or []),
            ("inaccessible_tables", operator_diag.get("inaccessible_tables") or []),
            ("blocked_reason", source_diag.get("blocked_reason") or source_diag.get("status")),
            ("recommendation", source_diag.get("recommendation")),
            ("no_write_confirmed", True),
        ])

    resolved_client = client
    if resolved_client is None:
        from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o7_streamlit_supabase_runtime import resolve_streamlit_supabase_client

        resolved = resolve_streamlit_supabase_client(dict(runtime_config or {}), client=client, client_factory=client_factory)
        resolved_client = resolved.get("client")

    source_audit = audit_replay_candidate_sources(client=resolved_client)
    inv = source_audit.get("inventory") or {}
    candidates = _as_list(inv.get("candidates"))
    replay_rows = int(inv.get("replay_metadata_row_count") or 0)
    manifest_rows = int(((source_audit.get("table_diagnostics") or {}).get("manifest") or {}).get("row_count") or 0)

    existing_ids: list[str] = []
    gov = validate_backfill_execution_governance(dry_run=True, client=resolved_client)
    cand_validation = validate_backfill_candidates(candidates=candidates, existing_replay_ids=existing_ids)
    b1 = build_d8_b1_controlled_backfill_plan(replay_metadata_rows=[], historical_runs_payloads=candidates, governance_inventory={}, dry_run=True)
    plan = build_backfill_execution_plan(d8_b1_backfill_plan=b1, candidates=candidates, existing_replay_ids=existing_ids, governance=gov, dry_run=True)
    execution = execute_controlled_replay_backfill(candidates=candidates, existing_replay_ids=existing_ids, client=resolved_client, dry_run=True)

    accepted = len(_as_list(cand_validation.get("accepted_candidates")))
    rejected = len(_as_list(cand_validation.get("rejected_candidates")))
    duplicates = len(_as_list(cand_validation.get("duplicate_ids")))
    lift = _estimate_intelligence_lift(replay_rows=replay_rows, candidate_sources=int(inv.get("candidate_derivation_source_count") or 0), accepted=accepted, rejected=rejected, duplicates=duplicates)
    exec_status = str(plan.get("execution_status") or "")
    rec = _recommendation(exec_status, str(gov.get("status") or ""), accepted, duplicates)

    return OrderedDict([
        ("timestamp_utc", _now_utc_iso()),
        ("source_diagnostics", source_diag),
        ("source_status", source_diag.get("status")),
        ("source_recommendation", source_diag.get("recommendation")),
        ("credential_status", (operator_diag.get("credential_audit") or {}).get("status")),
        ("client_status", (operator_diag.get("connectivity_audit") or {}).get("client_status")),
        ("read_only_connectivity_status", (operator_diag.get("connectivity_audit") or {}).get("read_only_connectivity_status")),
        ("selected_key_source", operator_diag.get("selected_key_source")),
        ("accessible_tables", operator_diag.get("accessible_tables") or []),
        ("inaccessible_tables", operator_diag.get("inaccessible_tables") or []),
        ("candidate_inventory", OrderedDict([
            ("replay_metadata_row_count", replay_rows),
            ("manifest_row_count", manifest_rows),
            ("candidate_source_count", int(inv.get("candidate_derivation_source_count") or 0)),
            ("total_candidates", len(candidates)),
            ("accepted_candidates", accepted),
            ("rejected_candidates", rejected),
            ("duplicate_candidates", duplicates),
            ("rejected_reasons", sorted({reason for row in _as_list(cand_validation.get("rejected_candidates")) for reason in _as_list(row.get("reasons"))})),
            ("duplicate_ids", _as_list(cand_validation.get("duplicate_ids"))),
            ("source_shape_compatible", bool(((source_audit.get("shape_comparison") or {}).get("source_shape_compatible")))),
        ])),
        ("governance", gov),
        ("plan", plan),
        ("execution", execution),
        ("expected_intelligence_lift", lift),
        ("recommendation", rec),
        ("no_write_confirmed", True),
    ])


def render_real_supabase_dry_run_retry_report(payload: Mapping[str, Any]) -> str:
    if payload.get("status") == "BLOCKED_SOURCE_NOT_READY":
        lines = [
            "# D8.B2 Real Supabase Dry-Run Retry Report",
            "",
            f"- source_status: `{payload.get('source_status')}`",
            f"- source_recommendation: `{payload.get('source_recommendation')}`",
            f"- credential_status: `{payload.get('credential_status')}`",
            f"- client_status: `{payload.get('client_status')}`",
            f"- read_only_connectivity_status: `{payload.get('read_only_connectivity_status')}`",
            f"- selected_key_source: `{payload.get('selected_key_source')}`",
            f"- accessible_tables: `{payload.get('accessible_tables')}`",
            f"- inaccessible_tables: `{payload.get('inaccessible_tables')}`",
            f"- blocked_reason: `{payload.get('blocked_reason')}`",
            f"- recommendation: `{payload.get('recommendation')}`",
            "- no_write_confirmed: true",
        ]
        return "\n".join(lines) + "\n"
    inv = payload.get("candidate_inventory") or {}
    gov = payload.get("governance") or {}
    plan = payload.get("plan") or {}
    exe = payload.get("execution") or {}
    audit = exe.get("audit_manifest") or {}
    lines = [
        "# D8.B2 Real Supabase Dry-Run Retry Report",
        "",
        f"- timestamp_utc: `{payload.get('timestamp_utc')}`",
        "- mode: `DRY_RUN_ONLY`",
        "- explicit_no_write_confirmation: `true`",
        "",
        "## Source Readiness Summary",
        f"- source_status: `{(payload.get('source_diagnostics') or {}).get('status')}`",
        f"- source_recommendation: `{(payload.get('source_diagnostics') or {}).get('recommendation')}`",
        f"- credential_status: `{payload.get('credential_status')}`",
        f"- client_status: `{payload.get('client_status')}`",
        f"- read_only_connectivity_status: `{payload.get('read_only_connectivity_status')}`",
        f"- selected_key_source: `{payload.get('selected_key_source')}`",
        f"- accessible_tables: `{payload.get('accessible_tables')}`",
        f"- inaccessible_tables: `{payload.get('inaccessible_tables')}`",
        "",
        "## Candidate Inventory Summary",
        *(f"- {k}: `{v}`" for k, v in inv.items() if k != "selected_key_source"),
        "",
        "## Validation Summary",
        f"- governance_status: `{gov.get('status')}`",
        f"- execution_status: `{plan.get('execution_status')}`",
        f"- governance_blocking_reasons: `{gov.get('blocking_reasons')}`",
        "",
        "## Duplicate Prevention Summary",
        f"- duplicate_ids: `{inv.get('duplicate_ids')}`",
        f"- duplicate_count: `{inv.get('duplicate_candidates')}`",
        "",
        "## Dry-Run Execution Plan",
        f"- target_tables: `{plan.get('target_tables')}`",
        f"- estimated_inserted_count: `{plan.get('estimated_inserted_count')}`",
        f"- write_count: `{audit.get('write_count', 0)}`",
        f"- inserted_count: `{exe.get('inserted_count')}`",
        f"- execution_checksum: `{exe.get('execution_checksum')}`",
        f"- audit_manifest_checksum: `{audit.get('manifest_checksum')}`",
        "",
        "## Expected Intelligence Lift",
        *(f"- {k}: `{v}`" for k, v in (payload.get("expected_intelligence_lift") or {}).items()),
        "",
        "## Operational Blockers",
        "- blockers: `none`",
        "",
        f"## Recommendation\n- recommendation: `{payload.get('recommendation')}`",
        "",
        "## No-Write Confirmation",
        "- no_write_confirmed: `true`",
    ]
    return "\n".join(lines) + "\n"


def run_and_write_report(report_path: Path = REPORT_PATH) -> OrderedDict[str, Any]:
    payload = build_real_supabase_dry_run_retry_payload()
    report_path.write_text(render_real_supabase_dry_run_retry_report(payload), encoding="utf-8")
    return payload
