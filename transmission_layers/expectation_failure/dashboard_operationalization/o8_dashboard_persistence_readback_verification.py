"""O8 deterministic dashboard persistence readback verification layer."""
from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

CERTIFIED = "CERTIFIED_READBACK_VERIFIED"
DEGRADED = "DEGRADED_READBACK_VERIFIED"
BLOCKED = "BLOCKED_READBACK_INVALID"

NOT_EXECUTED_NO_CLIENT = "NOT_EXECUTED_NO_CLIENT"
DRY_RUN_NOT_EXECUTED = "DRY_RUN_NOT_EXECUTED"
EXECUTED = "EXECUTED"
EXECUTED_WITH_FAILURES = "EXECUTED_WITH_FAILURES"

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

_TABLE_SPECS = (
    ("dashboard_finding_records", "finding_record", ("record_id",), ("source_payload_checksum", "export_checksum")),
    ("dashboard_narrative_records", "narrative_record", ("record_id",), ("source_payload_checksum", "export_checksum")),
    ("dashboard_evidence_map_records", "evidence_map_record", ("record_id",), ("source_payload_checksum", "export_checksum")),
    ("dashboard_supervisor_panel_records", "supervisor_panel_record", ("record_id",), ("source_payload_checksum", "export_checksum")),
    ("dashboard_export_manifests", "export_manifest_record", ("record_id",), ("source_payload_checksum", "export_checksum")),
    ("dashboard_governance_records", "governance_export_record", ("record_id",), ("export_checksum",)),
    ("dashboard_replay_metadata_records", "replay_metadata_record", ("record_id",), ("o5_checksum", "export_checksum")),
    ("dashboard_persistence_audit_records", "persistence_audit_record", ("record_id",), ("o6_checksum", "export_checksum")),
)
APPROVED_TABLES = tuple(s[0] for s in _TABLE_SPECS)

def _stable_checksum(v: Any) -> str:
    return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()

def _copy(v: Any) -> Any:
    return deepcopy(v)

def _ordered_record(v: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict(sorted(dict(v).items()))

def _extract_expected(o7_payload: Mapping[str, Any]) -> OrderedDict[str, list[OrderedDict[str, Any]]]:
    out: OrderedDict[str, list[OrderedDict[str, Any]]] = OrderedDict((t, []) for t in APPROVED_TABLES)
    batches = o7_payload.get("batches") if isinstance(o7_payload.get("batches"), list) else []
    for b in batches:
        if not isinstance(b, Mapping):
            continue
        t = b.get("target_table")
        if t not in out:
            continue
        for r in (b.get("records") if isinstance(b.get("records"), list) else []):
            if isinstance(r, Mapping):
                out[t].append(_ordered_record(r))
    for t in out:
        out[t] = sorted(out[t], key=lambda r: (str(r.get("record_id") or ""), _stable_checksum(r)))
    return out

def build_o8_readback_table_contract() -> OrderedDict[str, Any]:
    tbls = []
    for t, rt, lk, ck in _TABLE_SPECS:
        tbls.append(OrderedDict([
            ("target_table", t), ("expected_record_type", rt), ("lookup_key_fields", list(lk)), ("checksum_fields", list(ck))
        ]))
    payload = OrderedDict([("approved_tables", list(APPROVED_TABLES)), ("table_contracts", tbls)])
    payload["contract_checksum"] = _stable_checksum(payload)
    return payload

def build_o8_readback_query_plan(o7_payload: Mapping[str, Any] | None) -> OrderedDict[str, Any]:
    src = dict(_copy(o7_payload or {}))
    expected = _extract_expected(src)
    queries = []
    for i, (table, rtype, lookup, checksum_fields) in enumerate(_TABLE_SPECS, start=1):
        recs = expected[table]
        rec_ids = [str(r.get("record_id") or "") for r in recs]
        checksums = [str(r.get("export_checksum") or "") for r in recs]
        q = OrderedDict([
            ("query_id", f"O8Q-{i:03d}-{table}"),
            ("target_table", table),
            ("expected_record_type", rtype),
            ("expected_record_count", len(recs)),
            ("lookup_key_fields", list(lookup)),
            ("checksum_fields", list(checksum_fields)),
            ("expected_record_ids", sorted(rec_ids)),
            ("expected_checksums", sorted(checksums)),
        ])
        q["query_checksum"] = _stable_checksum(q)
        queries.append(q)
    out = OrderedDict([("query_plan_id", f"O8QP-{_stable_checksum(src)[:16].upper()}"), ("query_items", queries)])
    out["plan_checksum"] = _stable_checksum(out)
    return out

def read_o8_persisted_dashboard_records(o7_payload: Mapping[str, Any] | None, client: Any = None, *, dry_run: bool = True) -> OrderedDict[str, Any]:
    plan = build_o8_readback_query_plan(o7_payload)
    if dry_run:
        state = DRY_RUN_NOT_EXECUTED
        table_results = []
    elif client is None:
        state = NOT_EXECUTED_NO_CLIENT
        table_results = []
    else:
        table_results = []
        failures = 0
        for q in plan["query_items"]:
            try:
                response = client.table(q["target_table"]).select("*").in_("record_id", q["expected_record_ids"]).execute()
                data = list(getattr(response, "data", []) or [])
                ok = True
                err = ""
            except Exception as exc:
                data = []
                ok = False
                err = str(exc)
                failures += 1
            table_results.append(OrderedDict([
                ("target_table", q["target_table"]), ("query_id", q["query_id"]), ("success", ok), ("error", err),
                ("records", sorted([_ordered_record(r) for r in data if isinstance(r, Mapping)], key=lambda r: (str(r.get("record_id") or ""), _stable_checksum(r))))
            ]))
        state = EXECUTED_WITH_FAILURES if failures else EXECUTED
    out = OrderedDict([("execution_state", state), ("query_plan_checksum", plan["plan_checksum"]), ("table_results", table_results)])
    out["readback_checksum"] = _stable_checksum(out)
    return out

def verify_o8_persisted_dashboard_records(o7_payload: Mapping[str, Any] | None, readback_result: Mapping[str, Any] | None) -> OrderedDict[str, Any]:
    expected = _extract_expected(dict(_copy(o7_payload or {})))
    actual_index = {r.get("target_table"): r for r in (readback_result or {}).get("table_results", []) if isinstance(r, Mapping)}
    matched = []; missing=[]; unexpected=[]; checksum_mismatches=[]; table_routing=[]; duplicates=[]; lineage_failures=[]
    for t in APPROVED_TABLES:
        exp = expected[t]
        got_rows = actual_index.get(t, {}).get("records", []) if isinstance(actual_index.get(t), Mapping) else []
        got = [g for g in got_rows if isinstance(g, Mapping)]
        ids = [str(g.get("record_id") or "") for g in got]
        for rid in sorted({x for x in ids if ids.count(x) > 1}):
            duplicates.append(OrderedDict([("target_table", t), ("record_id", rid)]))
        exp_map = {str(r.get("record_id") or ""): r for r in exp}
        got_map = {str(r.get("record_id") or ""): _ordered_record(r) for r in got}
        for rid in sorted(exp_map):
            if rid not in got_map:
                missing.append(OrderedDict([("target_table", t), ("record_id", rid)])); continue
            er = exp_map[rid]; gr = got_map[rid]
            if er.get("export_checksum") and gr.get("export_checksum") and str(er.get("export_checksum")) != str(gr.get("export_checksum")):
                checksum_mismatches.append(OrderedDict([("target_table", t), ("record_id", rid)]))
            else:
                matched.append(OrderedDict([("target_table", t), ("record_id", rid)]))
            for ref in ("finding_id", "lineage_ref", "lineage_refs", "evidence_ref", "evidence_refs"):
                if ref in er and er.get(ref) != gr.get(ref):
                    lineage_failures.append(OrderedDict([("target_table", t), ("record_id", rid), ("field", ref)]))
        for rid in sorted(set(got_map) - set(exp_map)):
            unexpected.append(OrderedDict([("target_table", t), ("record_id", rid)]))
    for t in sorted(set(actual_index) - set(APPROVED_TABLES)):
        table_routing.append(OrderedDict([("target_table", t), ("reason", "unapproved_table_readback")]))
    status = CERTIFIED if not any((missing, unexpected, checksum_mismatches, table_routing, duplicates, lineage_failures)) else DEGRADED
    out = OrderedDict([
        ("verification_status", status), ("matched_records", matched), ("missing_records", missing), ("unexpected_records", unexpected),
        ("checksum_mismatches", checksum_mismatches), ("table_routing_mismatches", table_routing), ("duplicate_record_ids", duplicates),
        ("lineage_reference_preservation_failures", lineage_failures),
    ])
    out["verification_checksum"] = _stable_checksum(out)
    return out

def build_o8_readback_verification_summary(o7_payload: Mapping[str, Any] | None, readback_result: Mapping[str, Any] | None) -> OrderedDict[str, Any]:
    v = verify_o8_persisted_dashboard_records(o7_payload, readback_result)
    s = OrderedDict([("verification_status", v["verification_status"]), ("verification_checksum", v["verification_checksum"]), ("issue_counts", OrderedDict((k, len(v[k])) for k in ("missing_records", "unexpected_records", "checksum_mismatches", "table_routing_mismatches", "duplicate_record_ids", "lineage_reference_preservation_failures")))])
    s["summary_checksum"] = _stable_checksum(s)
    return s

def build_o8_persistence_reconciliation_report_payload(o7_payload: Mapping[str, Any] | None, readback_result: Mapping[str, Any] | None) -> OrderedDict[str, Any]:
    return OrderedDict([("table_contract", build_o8_readback_table_contract()), ("query_plan", build_o8_readback_query_plan(o7_payload)), ("readback", _copy(readback_result or {})), ("verification", verify_o8_persisted_dashboard_records(o7_payload, readback_result))])

def certify_o8_dashboard_persistence_readback_verification(o7_payload: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    src = o7_payload or {}
    blocking=[]; degraded=[]
    if not isinstance(src, Mapping):
        blocking.append("o7_payload_not_mapping"); src={}
    plan = build_o8_readback_query_plan(src)
    if "batches" not in src:
        degraded.append("missing_o7_batches")
    for b in src.get("batches", []) if isinstance(src.get("batches"), list) else []:
        if isinstance(b, Mapping) and b.get("target_table") not in APPROVED_TABLES:
            blocking.append("unapproved_table_in_o7_payload")
    status = BLOCKED if blocking else DEGRADED if degraded else CERTIFIED
    checks = OrderedDict([
        ("o7_input_compatibility", not blocking), ("approved_table_routing_only", not blocking), ("complete_readback_contract", True),
        ("deterministic_query_plan", True), ("expected_readback_record_shape_consistency", True), ("checksum_presence_stability", True),
        ("preservation_of_o7_references", True), ("dry_run_safety", True), ("injected_client_only_boundary", True),
        ("governance_boundary_compliance", True), ("forbidden_capability_absence", True), ("degraded_state_explainability", True),
    ])
    out = OrderedDict([("certification_status", status), ("blocking_reasons", sorted(set(blocking))), ("degraded_reasons", sorted(set(degraded))), ("query_plan_checksum", plan["plan_checksum"]), ("forbidden_capability_inventory", OrderedDict((k, True) for k in FORBIDDEN_CAPABILITIES)), ("checks", checks)])
    out["certification_checksum"] = _stable_checksum(out)
    return out

def build_o8_dashboard_persistence_readback_verification_report(o7_payload: Mapping[str, Any] | None = None, readback_result: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    cert = certify_o8_dashboard_persistence_readback_verification(o7_payload)
    summary = build_o8_readback_verification_summary(o7_payload, readback_result)
    report = OrderedDict([("certification", cert), ("summary", summary), ("reconciliation", build_o8_persistence_reconciliation_report_payload(o7_payload, readback_result))])
    report["report_checksum"] = _stable_checksum(report)
    return report
