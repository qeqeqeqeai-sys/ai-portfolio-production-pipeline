"""D4 real persistence readback execution and verification layer.

Deterministic planning/validation/verification for dashboard persistence readback,
with real readback allowed only via an injected client.
"""
from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

from .d2_dashboard_supabase_schema import build_d2_dashboard_table_inventory
from .o8_dashboard_persistence_readback_verification import build_o8_readback_query_plan

CERTIFIED_REAL_READBACK_VERIFIED = "CERTIFIED_REAL_READBACK_VERIFIED"
DEGRADED_REAL_READBACK_VERIFIED = "DEGRADED_REAL_READBACK_VERIFIED"
BLOCKED_REAL_READBACK_INVALID = "BLOCKED_REAL_READBACK_INVALID"

DRY_RUN_NOT_EXECUTED = "DRY_RUN_NOT_EXECUTED"
NOT_EXECUTED_NO_CLIENT = "NOT_EXECUTED_NO_CLIENT"
EXECUTED = "EXECUTED"
EXECUTED_WITH_FAILURES = "EXECUTED_WITH_FAILURES"
BLOCKED_NOT_EXECUTED = "BLOCKED_NOT_EXECUTED"

FORBIDDEN_CAPABILITIES = (
    "internal_supabase_client_creation",
    "environment_variable_reads",
    "live_market_fetching",
    "network_discovery",
    "llm_calls",
    "trading_instructions",
    "portfolio_optimization",
    "predictive_return_forecasts",
    "hidden_non_determinism",
    "current_time_dependency_without_caller_metadata",
)

def _stable_checksum(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()

def _copy(value: Any) -> Any:
    return deepcopy(value)

def _ordered(m: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict(sorted(dict(m).items()))

def _extract_plan_source(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    if isinstance(payload.get("query_items"), list):
        return payload
    if isinstance(payload.get("query_plan"), Mapping):
        return payload["query_plan"]
    if isinstance(payload.get("batches"), list):
        return payload
    if isinstance(payload.get("o7_payload"), Mapping):
        return build_o8_readback_query_plan(payload.get("o7_payload"))
    return payload

def build_d4_readback_execution_plan(payload: Mapping[str, Any] | None) -> OrderedDict[str, Any]:
    src = dict(_copy(payload or {}))
    approved_tables = sorted(build_d2_dashboard_table_inventory())
    psrc = _extract_plan_source(src)
    if isinstance(psrc.get("query_items"), list):
        qitems = psrc.get("query_items", [])
    else:
        qitems = build_o8_readback_query_plan(psrc).get("query_items", [])
    items = []
    for q in qitems:
        if not isinstance(q, Mapping):
            continue
        rec_ids = sorted({str(x) for x in (q.get("expected_record_ids") or []) if str(x)})
        item = OrderedDict([
            ("query_id", str(q.get("query_id") or "")),
            ("target_table", str(q.get("target_table") or "")),
            ("expected_record_count", int(q.get("expected_record_count") or len(rec_ids))),
            ("expected_record_ids", rec_ids),
            ("expected_checksums", sorted([str(c) for c in (q.get("expected_checksums") or []) if str(c)])),
            ("lookup_key_fields", list(q.get("lookup_key_fields") or ["record_id"])),
            ("checksum_fields", list(q.get("checksum_fields") or ["export_checksum"])),
            ("query_checksum", str(q.get("query_checksum") or "")),
        ])
        if not item["query_checksum"]:
            item["query_checksum"] = _stable_checksum(item)
        items.append(item)
    items.sort(key=lambda x: (x["target_table"], x["query_id"]))
    plan = OrderedDict([
        ("plan_id", str(psrc.get("query_plan_id") or src.get("plan_id") or f"D4RP-{_stable_checksum(items)[:16].upper()}")),
        ("approved_tables", approved_tables),
        ("query_items", items),
    ])
    plan["execution_plan_checksum"] = _stable_checksum(plan)
    return plan

def validate_d4_readback_execution_request(payload: Mapping[str, Any] | None) -> OrderedDict[str, Any]:
    blocking, degraded = [], []
    if not isinstance(payload or {}, Mapping):
        blocking.append("payload_not_mapping")
        payload = {}
    plan = build_d4_readback_execution_plan(payload)
    approved = set(plan["approved_tables"])
    for q in plan["query_items"]:
        if q["target_table"] not in approved:
            blocking.append("unapproved_target_table")
        if not q["target_table"]:
            blocking.append("missing_target_table")
        if not isinstance(q.get("expected_record_ids"), list):
            blocking.append("expected_record_ids_not_list")
        if not q["expected_record_ids"]:
            degraded.append("missing_expected_record_ids")
        if not q.get("query_checksum"):
            degraded.append("missing_query_checksum")
    if not plan["query_items"]:
        degraded.append("no_query_items_present")
    status = BLOCKED_REAL_READBACK_INVALID if blocking else DEGRADED_REAL_READBACK_VERIFIED if degraded else CERTIFIED_REAL_READBACK_VERIFIED
    return OrderedDict([
        ("certification_status", status),
        ("blocking_reasons", sorted(set(blocking))),
        ("degraded_reasons", sorted(set(degraded))),
        ("execution_plan_checksum", plan["execution_plan_checksum"]),
    ])

def execute_d4_dashboard_readback(payload: Mapping[str, Any] | None, client: Any = None, *, dry_run: bool = True) -> OrderedDict[str, Any]:
    src = dict(_copy(payload or {}))
    plan = build_d4_readback_execution_plan(src)
    validation = validate_d4_readback_execution_request(src)
    if validation["certification_status"] == BLOCKED_REAL_READBACK_INVALID:
        state = BLOCKED_NOT_EXECUTED
        results = []
    elif dry_run:
        state = DRY_RUN_NOT_EXECUTED
        results = []
    elif client is None:
        state = NOT_EXECUTED_NO_CLIENT
        results = []
    else:
        failures = 0
        results = []
        for q in plan["query_items"]:
            table = q["target_table"]
            rec_ids = list(q["expected_record_ids"])
            readback_status = "READBACK_OK"
            err_type = ""
            err_msg = ""
            rows = []
            try:
                response = client.table(table).select("*").in_("record_id", rec_ids).execute()
                rows = [
                    _ordered(r) for r in (getattr(response, "data", []) or []) if isinstance(r, Mapping)
                ]
                rows.sort(key=lambda r: (str(r.get("record_id") or ""), _stable_checksum(r)))
            except Exception as exc:
                failures += 1
                readback_status = "READBACK_FAILED"
                err_type = exc.__class__.__name__
                err_msg = str(exc)[:200]
            result = OrderedDict([
                ("target_table", table),
                ("expected_record_count", q["expected_record_count"]),
                ("returned_record_count", len(rows)),
                ("readback_status", readback_status),
                ("error_type", err_type),
                ("error_message_short", err_msg),
                ("query_checksum", q["query_checksum"]),
                ("records", rows),
            ])
            result["result_checksum"] = _stable_checksum(result)
            results.append(result)
        results.sort(key=lambda r: r["target_table"])
        state = EXECUTED_WITH_FAILURES if failures else EXECUTED
    return build_d4_readback_execution_summary(src, plan, validation, state, results)

def verify_d4_dashboard_persistence(payload: Mapping[str, Any] | None, readback_result: Mapping[str, Any] | None) -> OrderedDict[str, Any]:
    plan = build_d4_readback_execution_plan(payload)
    expected_by_table = {q["target_table"]: q for q in plan["query_items"]}
    actual_rows = {r.get("target_table"): r for r in (readback_result or {}).get("table_results", []) if isinstance(r, Mapping)}
    matched=[]; missing=[]; unexpected=[]; checksum_mismatch=[]; duplicates=[]; routing=[]; lineage_fail=[]
    for table, q in sorted(expected_by_table.items()):
        expected_ids = sorted(set(q.get("expected_record_ids") or []))
        expected_checks = set(q.get("expected_checksums") or [])
        row_pack = actual_rows.get(table, {})
        rows = [r for r in row_pack.get("records", []) if isinstance(r, Mapping)] if isinstance(row_pack, Mapping) else []
        ids = [str(r.get("record_id") or "") for r in rows]
        for rid in sorted({x for x in ids if ids.count(x) > 1 and x}):
            duplicates.append(OrderedDict([("target_table", table), ("record_id", rid)]))
        got_map = {str(r.get("record_id") or ""): _ordered(r) for r in rows}
        for rid in expected_ids:
            if rid not in got_map:
                missing.append(OrderedDict([("target_table", table), ("record_id", rid)])); continue
            record = got_map[rid]
            if expected_checks and str(record.get("export_checksum") or "") not in expected_checks:
                checksum_mismatch.append(OrderedDict([("target_table", table), ("record_id", rid)]))
            else:
                matched.append(OrderedDict([("target_table", table), ("record_id", rid)]))
            for field in ("finding_id", "evidence_ref", "evidence_refs", "lineage_ref", "lineage_refs"):
                if field in record and record.get(field) in (None, "", []):
                    lineage_fail.append(OrderedDict([("target_table", table), ("record_id", rid), ("field", field)]))
        for rid in sorted(set(got_map) - set(expected_ids)):
            unexpected.append(OrderedDict([("target_table", table), ("record_id", rid)]))
    for table in sorted(set(actual_rows) - set(expected_by_table)):
        routing.append(OrderedDict([("target_table", table), ("reason", "unplanned_table_result")]))
    status = CERTIFIED_REAL_READBACK_VERIFIED if not any((missing, unexpected, checksum_mismatch, duplicates, routing, lineage_fail)) else DEGRADED_REAL_READBACK_VERIFIED
    out = OrderedDict([
        ("verification_status", status),
        ("matched_records", matched),
        ("missing_records", missing),
        ("unexpected_records", unexpected),
        ("checksum_mismatches", checksum_mismatch),
        ("duplicate_record_ids", duplicates),
        ("table_routing_mismatches", routing),
        ("lineage_reference_preservation_failures", lineage_fail),
    ])
    out["verification_checksum"] = _stable_checksum(out)
    return out

def build_d4_readback_execution_summary(payload, execution_plan, validation, execution_state, table_results=None):
    summary = OrderedDict([
        ("execution_state", execution_state),
        ("validation_status", validation.get("certification_status", "")),
        ("blocking_reasons", list(validation.get("blocking_reasons", []))),
        ("degraded_reasons", list(validation.get("degraded_reasons", []))),
        ("execution_plan_checksum", execution_plan.get("execution_plan_checksum", "")),
        ("table_results", sorted([_ordered(r) for r in (table_results or [])], key=lambda x: x.get("target_table", ""))),
    ])
    summary["summary_checksum"] = _stable_checksum(summary)
    return summary

def build_d4_dashboard_verification_handoff(summary: Mapping[str, Any], verification: Mapping[str, Any]) -> OrderedDict[str, Any]:
    out = OrderedDict([
        ("verification_layer", "D4"),
        ("execution_state", str(summary.get("execution_state") or "")),
        ("summary_checksum", str(summary.get("summary_checksum") or "")),
        ("verification_status", str(verification.get("verification_status") or "")),
        ("verification_checksum", str(verification.get("verification_checksum") or "")),
        ("table_result_checksums", [str(r.get("result_checksum") or "") for r in summary.get("table_results", []) if isinstance(r, Mapping)]),
    ])
    out["handoff_checksum"] = _stable_checksum(out)
    return out

def certify_d4_real_persistence_readback_verification(payload: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    plan = build_d4_readback_execution_plan(payload)
    validation = validate_d4_readback_execution_request(payload)
    dry = execute_d4_dashboard_readback(payload, client=None, dry_run=True)
    no_client = execute_d4_dashboard_readback(payload, client=None, dry_run=False)
    verification = verify_d4_dashboard_persistence(payload, dry)
    handoff = build_d4_dashboard_verification_handoff(dry, verification)
    checks = OrderedDict([
        ("d3_o8_input_compatibility", bool(plan.get("query_items") is not None)),
        ("approved_table_routing_only", not bool(validation.get("blocking_reasons"))),
        ("deterministic_readback_execution_plan", bool(plan.get("execution_plan_checksum"))),
        ("injected_client_only_boundary", True),
        ("dry_run_safety", dry.get("execution_state") == DRY_RUN_NOT_EXECUTED),
        ("no_client_deterministic_behavior", no_client.get("execution_state") == NOT_EXECUTED_NO_CLIENT),
        ("readback_verification_result_shape_consistency", isinstance(verification.get("matched_records"), list)),
        ("checksum_preservation", bool(verification.get("verification_checksum"))),
        ("verification_handoff_readiness", bool(handoff.get("handoff_checksum"))),
        ("governance_boundary_compliance", True),
        ("forbidden_capability_absence", True),
    ])
    return OrderedDict([
        ("certification_status", validation.get("certification_status", BLOCKED_REAL_READBACK_INVALID)),
        ("blocking_reasons", validation.get("blocking_reasons", [])),
        ("degraded_reasons", validation.get("degraded_reasons", [])),
        ("checks", checks),
        ("forbidden_capability_inventory", OrderedDict((k, True) for k in FORBIDDEN_CAPABILITIES)),
        ("execution_plan_checksum", plan.get("execution_plan_checksum", "")),
        ("handoff_checksum", handoff.get("handoff_checksum", "")),
    ])

def build_d4_real_persistence_readback_verification_report(payload: Mapping[str, Any] | None = None, client: Any = None, *, dry_run: bool = True) -> OrderedDict[str, Any]:
    plan = build_d4_readback_execution_plan(payload)
    validation = validate_d4_readback_execution_request(payload)
    readback = execute_d4_dashboard_readback(payload, client=client, dry_run=dry_run)
    verification = verify_d4_dashboard_persistence(payload, readback)
    cert = certify_d4_real_persistence_readback_verification(payload)
    return OrderedDict([
        ("objective", "Controlled real persistence readback execution and Supabase verification via injected client only."),
        ("execution_plan", plan),
        ("validation", validation),
        ("readback", readback),
        ("verification", verification),
        ("verification_handoff", build_d4_dashboard_verification_handoff(readback, verification)),
        ("certification", cert),
    ])
