from __future__ import annotations

from collections import OrderedDict
import hashlib
import json
from datetime import datetime
from typing import Any, Mapping

from .d8_b1_controlled_replay_expansion import build_d8_b1_controlled_backfill_plan
from .d8_b2r_replay_candidate_source_repair_audit import (
    audit_replay_candidate_sources,
    audit_supabase_client_resolution,
    build_d8_b2r2_runtime_connectivity_bundle,
    build_d8_b2r_source_repair_report_payload,
)

D8_B2_VERSION = "d8_b2_controlled_replay_backfill_execution_v1"

_ALLOWED_TABLES = ("dashboard_replay_metadata_records",)
_FORBIDDEN_CAPABILITIES = {
    "network_calls", "live_fetch", "trading_logic", "prediction_logic", "black_box_ml", "hidden_writes",
}


def _stable_checksum(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _as_text(v: Any) -> str:
    return str(v).strip() if v is not None else ""


def _as_list(v: Any) -> list[Any]:
    return list(v) if isinstance(v, list) else []


def _is_iso_utc(ts: str) -> bool:
    if not ts or not ts.endswith("Z"):
        return False
    try:
        datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def validate_backfill_execution_governance(*, dry_run: bool = True, client: Any = None, approval_flags: Mapping[str, Any] | None = None, allowed_tables: list[str] | None = None, forbidden_capabilities: Mapping[str, Any] | None = None, append_only: bool = True, duplicate_prevention: bool = True, checksum_lineage: bool = True) -> OrderedDict[str, Any]:
    flags = dict(approval_flags or {})
    inventory = set(allowed_tables or list(_ALLOWED_TABLES))
    caps = dict(forbidden_capabilities or {})
    blocking: list[str] = []
    if not dry_run:
        if client is None:
            blocking.append("missing_injected_client")
        if not bool(flags.get("approved_for_execution")):
            blocking.append("missing_execution_approval")
        if not bool(flags.get("approved_by_governance")):
            blocking.append("missing_governance_approval")
    if not inventory or not inventory.issubset(set(_ALLOWED_TABLES)):
        blocking.append("unapproved_table_inventory")
    if not append_only:
        blocking.append("append_only_policy_required")
    if not duplicate_prevention:
        blocking.append("duplicate_prevention_policy_required")
    if not checksum_lineage:
        blocking.append("checksum_lineage_policy_required")
    for cap in sorted(_FORBIDDEN_CAPABILITIES):
        if bool(caps.get(cap)):
            blocking.append(f"forbidden_capability_enabled:{cap}")
    status = "GOVERNANCE_OK" if not blocking else "GOVERNANCE_BLOCKED"
    payload = OrderedDict([
        ("status", status),
        ("dry_run", bool(dry_run)),
        ("allowed_tables", sorted(inventory)),
        ("blocking_reasons", sorted(set(blocking))),
    ])
    payload["governance_checksum"] = _stable_checksum(payload)
    return payload


def validate_backfill_candidates(*, candidates: list[Mapping[str, Any]], existing_replay_ids: list[str] | None = None) -> OrderedDict[str, Any]:
    existing = {_as_text(x) for x in _as_list(existing_replay_ids) if _as_text(x)}
    seen: set[str] = set()
    accepted = []
    rejected = []
    duplicates = []
    for row in sorted([r for r in _as_list(candidates) if isinstance(r, Mapping)], key=lambda x: (_as_text(x.get("run_timestamp") or x.get("timestamp")), _as_text(x.get("run_id") or x.get("record_id")))):
        run_id = _as_text(row.get("run_id") or row.get("record_id") or row.get("replay_id"))
        ts = _as_text(row.get("run_timestamp") or row.get("timestamp"))
        checksum = _as_text(row.get("payload_checksum") or row.get("source_payload_checksum") or row.get("checksum_lineage"))
        source_trace = _as_text(row.get("source_trace") or row.get("source") or row.get("lineage_source"))
        synthetic = bool(row.get("is_synthetic") or row.get("synthetic_marker") or row.get("fabricated"))
        reasons = []
        if not run_id:
            reasons.append("missing_run_id")
        if not ts:
            reasons.append("missing_run_timestamp")
        elif not _is_iso_utc(ts):
            reasons.append("non_deterministic_timestamp")
        if not checksum:
            reasons.append("missing_checksum_lineage")
        if not source_trace:
            reasons.append("missing_source_trace")
        if synthetic:
            reasons.append("synthetic_marker_detected")
        if run_id and run_id in seen:
            reasons.append("duplicate_run_id_in_batch")
        if run_id and run_id in existing:
            reasons.append("already_present_in_replay_inventory")
        if reasons:
            rejected.append(OrderedDict([("run_id", run_id), ("reasons", sorted(set(reasons)))]))
            if any(r in {"duplicate_run_id_in_batch", "already_present_in_replay_inventory"} for r in reasons):
                duplicates.append(run_id)
        else:
            accepted.append(OrderedDict(sorted(dict(row).items())))
            seen.add(run_id)
    payload = OrderedDict([
        ("accepted_candidates", accepted),
        ("rejected_candidates", rejected),
        ("duplicate_ids", sorted({_as_text(x) for x in duplicates if _as_text(x)})),
    ])
    payload["candidate_validation_checksum"] = _stable_checksum(payload)
    return payload


def build_backfill_execution_plan(*, d8_b1_backfill_plan: Mapping[str, Any] | None = None, candidates: list[Mapping[str, Any]] | None = None, existing_replay_ids: list[str] | None = None, governance: Mapping[str, Any] | None = None, dry_run: bool = True, target_tables: list[str] | None = None) -> OrderedDict[str, Any]:
    b1_plan = OrderedDict(sorted(dict(d8_b1_backfill_plan or build_d8_b1_controlled_backfill_plan(replay_metadata_rows=[], historical_runs_payloads=[], governance_inventory={}, dry_run=True)).items()))
    candidate_validation = validate_backfill_candidates(candidates=_as_list(candidates), existing_replay_ids=existing_replay_ids)
    gov = dict(governance or {})
    governance_status = _as_text(gov.get("status")) or "GOVERNANCE_BLOCKED"
    accepted = _as_list(candidate_validation.get("accepted_candidates"))
    rejected = _as_list(candidate_validation.get("rejected_candidates"))
    duplicates = _as_list(candidate_validation.get("duplicate_ids"))
    if governance_status != "GOVERNANCE_OK":
        exec_status = "BACKFILL_BLOCKED_GOVERNANCE"
    elif rejected and len(rejected) == len(_as_list(candidates)):
        exec_status = "BACKFILL_BLOCKED_INVALID_CANDIDATES"
    elif duplicates:
        exec_status = "BACKFILL_BLOCKED_DUPLICATES"
    elif dry_run:
        exec_status = "BACKFILL_DRY_RUN_READY"
    else:
        exec_status = "BACKFILL_EXECUTION_READY"
    payload = OrderedDict([
        ("d8_b2_version", D8_B2_VERSION),
        ("dry_run", bool(dry_run)),
        ("governance_status", governance_status),
        ("candidate_count", len(_as_list(candidates))),
        ("accepted_count", len(accepted)),
        ("rejected_count", len(rejected)),
        ("duplicate_count", len(duplicates)),
        ("estimated_inserted_count", 0 if governance_status != "GOVERNANCE_OK" else len(accepted)),
        ("target_tables", sorted(set(target_tables or list(_ALLOWED_TABLES)))),
        ("checksum_manifest", OrderedDict([("b1_backfill_plan_checksum", _as_text(b1_plan.get("backfill_plan_checksum"))), ("candidate_validation_checksum", _as_text(candidate_validation.get("candidate_validation_checksum"))), ("governance_checksum", _as_text(gov.get("governance_checksum")))])),
        ("execution_status", exec_status),
        ("candidate_validation", candidate_validation),
    ])
    payload["execution_plan_checksum"] = _stable_checksum(payload)
    return payload


def build_backfill_audit_manifest(*, plan: Mapping[str, Any], governance: Mapping[str, Any], dry_run: bool, write_count: int) -> OrderedDict[str, Any]:
    validation = plan.get("candidate_validation") if isinstance(plan.get("candidate_validation"), Mapping) else {}
    rejected = _as_list(validation.get("rejected_candidates"))
    manifest = OrderedDict([
        ("candidate_ids", sorted([_as_text(x.get("run_id") or x.get("record_id")) for x in _as_list(validation.get("accepted_candidates")) + rejected if _as_text(x.get("run_id") or x.get("record_id"))])),
        ("accepted_ids", sorted([_as_text(x.get("run_id") or x.get("record_id")) for x in _as_list(validation.get("accepted_candidates")) if _as_text(x.get("run_id") or x.get("record_id"))])),
        ("rejected_ids_with_reasons", sorted([( _as_text(x.get("run_id")), sorted(_as_list(x.get("reasons"))) ) for x in rejected], key=lambda t: (t[0], ",".join(t[1])))),
        ("duplicate_ids", sorted(_as_list(validation.get("duplicate_ids")))),
        ("target_table_inventory", sorted(_as_list(plan.get("target_tables")))),
        ("checksum_lineage", OrderedDict(sorted(dict(plan.get("checksum_manifest") or {}).items()))),
        ("governance_flags", OrderedDict(sorted({"status": governance.get("status"), "blocking_reasons": governance.get("blocking_reasons", [])}.items()))),
        ("dry_run", bool(dry_run)),
        ("write_count", int(write_count)),
    ])
    manifest["manifest_checksum"] = _stable_checksum(manifest)
    return manifest


def execute_controlled_replay_backfill(*, candidates: list[Mapping[str, Any]], existing_replay_ids: list[str] | None = None, client: Any = None, dry_run: bool = True, approval_flags: Mapping[str, Any] | None = None, d8_b1_backfill_plan: Mapping[str, Any] | None = None, target_table: str = "dashboard_replay_metadata_records") -> OrderedDict[str, Any]:
    governance = validate_backfill_execution_governance(dry_run=dry_run, client=client, approval_flags=approval_flags, allowed_tables=[target_table])
    plan = build_backfill_execution_plan(d8_b1_backfill_plan=d8_b1_backfill_plan, candidates=candidates, existing_replay_ids=existing_replay_ids, governance=governance, dry_run=dry_run, target_tables=[target_table])
    if dry_run:
        return OrderedDict([("status", "BACKFILL_DRY_RUN_ONLY"), ("plan", plan), ("audit_manifest", build_backfill_audit_manifest(plan=plan, governance=governance, dry_run=True, write_count=0)), ("inserted_count", 0), ("execution_checksum", _stable_checksum(plan))])
    if governance.get("status") != "GOVERNANCE_OK":
        return OrderedDict([("status", "BACKFILL_BLOCKED_GOVERNANCE"), ("plan", plan), ("inserted_count", 0), ("execution_checksum", _stable_checksum(plan))])
    accepted = _as_list((plan.get("candidate_validation") or {}).get("accepted_candidates"))
    ordered = sorted(accepted, key=lambda x: (_as_text(x.get("run_timestamp") or x.get("timestamp")), _as_text(x.get("run_id") or x.get("record_id"))))
    write_count = 0
    if ordered:
        client.table(target_table).insert(ordered).execute()
        write_count = len(ordered)
    rejected_count = int(plan.get("rejected_count") or 0)
    duplicate_count = int(plan.get("duplicate_count") or 0)
    status = "BACKFILL_EXECUTED"
    if rejected_count > 0:
        status = "BACKFILL_PARTIAL_WITH_REJECTIONS"
    elif duplicate_count > 0:
        status = "BACKFILL_BLOCKED_DUPLICATES"
    audit = build_backfill_audit_manifest(plan=plan, governance=governance, dry_run=False, write_count=write_count)
    return OrderedDict([
        ("status", status),
        ("plan", plan),
        ("audit_manifest", audit),
        ("inserted_count", write_count),
        ("rejected_count", rejected_count),
        ("duplicate_count", duplicate_count),
        ("execution_checksum", _stable_checksum(OrderedDict([("plan", plan), ("audit", audit), ("inserted_count", write_count)]))),
    ])


def build_d8_b2_dry_run_source_diagnostics(*, runtime_config: Mapping[str, Any] | None = None, client: Any = None, client_factory: Any = None, findings: list[Mapping[str, Any]] | None = None, narratives: list[Mapping[str, Any]] | None = None, evidence_maps: list[Mapping[str, Any]] | None = None) -> OrderedDict[str, Any]:
    client_audit = audit_supabase_client_resolution(runtime_config=runtime_config, client=client, client_factory=client_factory)
    resolved_client = client if client_audit.get("client_resolved") else None
    source_audit = audit_replay_candidate_sources(client=resolved_client, findings=findings, narratives=narratives, evidence_maps=evidence_maps)
    runtime_bundle = build_d8_b2r2_runtime_connectivity_bundle(runtime_config=runtime_config, client=client, client_factory=client_factory)
    return build_d8_b2r_source_repair_report_payload(client_audit=client_audit, source_audit=source_audit, runtime_connectivity=runtime_bundle)
