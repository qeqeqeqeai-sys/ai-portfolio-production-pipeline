from __future__ import annotations

from collections import OrderedDict
from datetime import datetime, timezone
from typing import Any, Mapping

from transmission_layers.expectation_failure.dashboard_operationalization.d6_operational_proving_cycle import (
    execute_d6_operational_proving_cycle,
)
from transmission_layers.expectation_failure.expectation_intelligence.d8_b2_controlled_replay_backfill_execution import (
    validate_backfill_execution_governance,
)
from transmission_layers.expectation_failure.expectation_intelligence.d8_b2_real_supabase_dry_run_retry import (
    build_real_supabase_dry_run_retry_payload,
)
from transmission_layers.expectation_failure.expectation_intelligence.d8_b3_replay_persistence_activation_audit import (
    audit_replay_persistence_gates,
    audit_replay_persistence_pipeline,
)

APPROVED_REPLAY_TABLE = "dashboard_replay_metadata_records"
APPROVED_MANIFEST_TABLE = "dashboard_export_manifests"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _as_list(v: Any) -> list[Any]:
    return list(v) if isinstance(v, list) else []


def _txt(v: Any) -> str:
    return str(v).strip() if v is not None else ""


def validate_d8_b4_execution_governance(*, dry_run: bool, client: Any = None, approval_flags: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    flags = dict(approval_flags or {})
    base = validate_backfill_execution_governance(
        dry_run=dry_run,
        client=client,
        approval_flags=flags,
        allowed_tables=[APPROVED_REPLAY_TABLE],
        append_only=True,
        duplicate_prevention=True,
        checksum_lineage=True,
    )
    gates = audit_replay_persistence_gates(dry_run=dry_run, persistence_enabled=True, client_resolved=client is not None)
    pipeline = audit_replay_persistence_pipeline()
    blocked = list(_as_list(base.get("blocking_reasons")))
    if not dry_run:
        if flags.get("approve_non_dry_run") != "true":
            blocked.append("missing_non_dry_run_approval")
        if flags.get("approve_append_only_persistence") != "true":
            blocked.append("missing_append_only_persistence_approval")
        if flags.get("approve_duplicate_prevention") != "true":
            blocked.append("missing_duplicate_prevention_approval")
        if flags.get("approve_checksum_lineage") != "true":
            blocked.append("missing_checksum_lineage_approval")
    if not pipeline.get("is_wired"):
        blocked.append("replay_persistence_not_wired")
    approved_tables_present = bool(base.get("allowed_tables")) and set(_as_list(base.get("allowed_tables"))) == {APPROVED_REPLAY_TABLE}
    status = "GOVERNANCE_OK" if not blocked else "GOVERNANCE_BLOCKED"
    return OrderedDict([
        ("governance_status", status),
        ("status", status),
        ("blocking_reasons", sorted(set(blocked))),
        ("dry_run", bool(dry_run)),
        ("injected_client_present", client is not None),
        ("approval_flag_present", all(k in flags for k in ("approve_non_dry_run", "approve_append_only_persistence", "approve_duplicate_prevention", "approve_checksum_lineage"))),
        ("append_only_confirmed", flags.get("approve_append_only_persistence") == "true"),
        ("duplicate_prevention_confirmed", flags.get("approve_duplicate_prevention") == "true"),
        ("checksum_lineage_confirmed", flags.get("approve_checksum_lineage") == "true"),
        ("approved_tables_present", approved_tables_present),
        ("approval_flags", OrderedDict(sorted(flags.items()))),
        ("required_runtime_flags", OrderedDict([
            ("dry_run", bool(dry_run)),
            ("approved_for_execution", bool(flags.get("approved_for_execution"))),
            ("approved_by_governance", bool(flags.get("approved_by_governance"))),
            ("approve_non_dry_run", flags.get("approve_non_dry_run") == "true"),
            ("approve_append_only_persistence", flags.get("approve_append_only_persistence") == "true"),
            ("approve_duplicate_prevention", flags.get("approve_duplicate_prevention") == "true"),
            ("approve_checksum_lineage", flags.get("approve_checksum_lineage") == "true"),
            ("append_only", True),
        ])),
        ("required_injected_client_shape", ["table", "insert", "upsert", "select", "execute"]),
        ("pipeline", pipeline),
        ("persistence_gates", gates),
        ("append_only_guarantee", True),
    ])


def build_d8_b4_persistence_execution_plan(*, governance: Mapping[str, Any], dry_run: bool) -> OrderedDict[str, Any]:
    status = "EXECUTION_READY" if governance.get("status") == "GOVERNANCE_OK" and not dry_run else "EXECUTION_BLOCKED"
    return OrderedDict([
        ("execution_status", status),
        ("dry_run", bool(dry_run)),
        ("target_tables", [APPROVED_REPLAY_TABLE, APPROVED_MANIFEST_TABLE]),
        ("append_only", True),
        ("duplicate_prevention", ["record_id/replay_id", "checksum lineage"]),
        ("blocked_reasons", _as_list(governance.get("blocking_reasons"))),
    ])


def build_d8_b4_execution_audit_manifest(*, d6_result: Mapping[str, Any], governance: Mapping[str, Any], dry_run: bool) -> OrderedDict[str, Any]:
    d3 = d6_result.get("d3_persistence") or {}
    table_results = [r for r in _as_list(d3.get("table_results")) if isinstance(r, Mapping)]
    duplicate_ids = sorted({
        _txt(r.get("record_id") or r.get("replay_id"))
        for r in _as_list((d3.get("summary") or {}).get("rejected_records")) if isinstance(r, Mapping)
    } - {""})
    return OrderedDict([
        ("timestamp_utc", _now()),
        ("dry_run", bool(dry_run)),
        ("governance_status", governance.get("status")),
        ("attempted_inserts", int(sum(int(r.get("attempted_record_count") or 0) for r in table_results))),
        ("successful_inserts", int(sum(int(r.get("persisted_record_count") or 0) for r in table_results))),
        ("rejected_duplicates", len(duplicate_ids)),
        ("duplicate_ids", duplicate_ids),
        ("rejected_reasons", sorted(set(_as_list(governance.get("blocking_reasons"))))),
        ("append_only_confirmed", True),
    ])


def build_d8_b4_governance_diagnostics(*, result: Mapping[str, Any]) -> OrderedDict[str, Any]:
    governance = result.get("governance") or {}
    plan = result.get("plan") or {}
    report_payload = result.get("report_payload") or {}
    return OrderedDict([
        ("status", result.get("status")),
        ("governance_status", governance.get("status") or governance.get("governance_status")),
        ("blocking_reasons", _as_list(governance.get("blocking_reasons"))),
        ("dry_run", governance.get("dry_run")),
        ("injected_client_present", governance.get("injected_client_present")),
        ("approval_flag_present", governance.get("approval_flag_present")),
        ("append_only_confirmed", governance.get("append_only_confirmed")),
        ("duplicate_prevention_confirmed", governance.get("duplicate_prevention_confirmed")),
        ("checksum_lineage_confirmed", governance.get("checksum_lineage_confirmed")),
        ("approved_tables_present", governance.get("approved_tables_present")),
        ("execution_status", plan.get("execution_status")),
        ("recommendation", report_payload.get("recommendation") or result.get("status")),
    ])


def execute_d8_b4_governed_replay_persistence(*, client: Any, approval_flags: Mapping[str, Any] | None = None, dry_run: bool = False) -> OrderedDict[str, Any]:
    governance = validate_d8_b4_execution_governance(dry_run=dry_run, client=client, approval_flags=approval_flags)
    plan = build_d8_b4_persistence_execution_plan(governance=governance, dry_run=dry_run)
    if governance.get("status") != "GOVERNANCE_OK":
        return OrderedDict([("status", "REPLAY_PERSISTENCE_GOVERNANCE_BLOCKED"), ("governance", governance), ("plan", plan)])
    d6 = execute_d6_operational_proving_cycle(client=client, dry_run=dry_run)
    audit = build_d8_b4_execution_audit_manifest(d6_result=d6, governance=governance, dry_run=dry_run)
    readback = build_d8_b4_post_execution_readback(client=client)
    d8b2 = build_real_supabase_dry_run_retry_payload(client=client)
    report = build_d8_b4_execution_report_payload(governance=governance, plan=plan, audit=audit, readback=readback, d8_b2_retry=d8b2)
    return OrderedDict([("status", report.get("recommendation")), ("governance", governance), ("plan", plan), ("d6_result", d6), ("audit_manifest", audit), ("readback", readback), ("d8_b2_retry", d8b2), ("report_payload", report)])


def build_d8_b4_post_execution_readback(*, client: Any) -> OrderedDict[str, Any]:
    replay = client.table(APPROVED_REPLAY_TABLE).select("*").execute()
    manifest = client.table(APPROVED_MANIFEST_TABLE).select("*").execute()
    rr = _as_list(getattr(replay, "data", []) or [])
    mr = _as_list(getattr(manifest, "data", []) or [])
    return OrderedDict([
        ("replay_metadata_row_count", len(rr)),
        ("manifest_row_count", len(mr)),
        ("latest_replay_ids", sorted([_txt(r.get("replay_id") or r.get("record_id")) for r in rr if isinstance(r, Mapping) and _txt(r.get("replay_id") or r.get("record_id"))])[-5:]),
        ("latest_manifest_checksums", sorted([_txt(r.get("export_checksum") or r.get("manifest_checksum")) for r in mr if isinstance(r, Mapping) and _txt(r.get("export_checksum") or r.get("manifest_checksum"))])[-5:]),
        ("lineage_checksum_present", all(_txt(r.get("source_payload_checksum") or r.get("replay_checksum") or r.get("export_checksum")) for r in rr if isinstance(r, Mapping)) if rr else False),
        ("payload_completeness", all(bool(r) for r in rr + mr)),
        ("replay_candidate_readiness", "READY" if rr else "NOT_READY"),
    ])


def build_d8_b4_execution_report_payload(*, governance: Mapping[str, Any], plan: Mapping[str, Any], audit: Mapping[str, Any], readback: Mapping[str, Any], d8_b2_retry: Mapping[str, Any]) -> OrderedDict[str, Any]:
    if governance.get("status") != "GOVERNANCE_OK":
        rec = "REPLAY_PERSISTENCE_GOVERNANCE_BLOCKED"
    elif int(audit.get("successful_inserts") or 0) == 0:
        rec = "REPLAY_PERSISTENCE_DUPLICATE_BLOCKED"
    elif int(readback.get("replay_metadata_row_count") or 0) > 0 and int(readback.get("manifest_row_count") or 0) > 0:
        rec = "REPLAY_PERSISTENCE_OPERATIONAL"
    else:
        rec = "REPLAY_PERSISTENCE_PARTIAL"
    return OrderedDict([
        ("timestamp_utc", _now()),
        ("objective", "Governed non-dry replay persistence execution"),
        ("approved_chain", "O6 -> O7 -> D3 -> D6"),
        ("governance", governance),
        ("execution_plan", plan),
        ("audit", audit),
        ("post_execution_readback", readback),
        ("d8_b2_post_persistence", d8_b2_retry),
        ("recommendation", rec),
        ("no_direct_sql_bypass_used", True),
    ])
