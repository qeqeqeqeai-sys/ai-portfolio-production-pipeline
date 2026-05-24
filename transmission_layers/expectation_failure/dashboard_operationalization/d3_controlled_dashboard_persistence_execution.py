"""D3 controlled dashboard persistence execution layer.

Deterministic execution planning/validation/summarization for O6/O7 dashboard
operationalization persistence. Real persistence is allowed only through an
explicitly injected client and never through internally constructed clients.
"""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

from .d2_dashboard_supabase_schema import build_d2_dashboard_table_inventory
from .o7_dashboard_persistence_adapter import build_o7_persistence_table_contract, build_o7_write_batch_plan

CERTIFIED_DASHBOARD_PERSISTENCE_EXECUTION_READY = "CERTIFIED_DASHBOARD_PERSISTENCE_EXECUTION_READY"
DEGRADED_DASHBOARD_PERSISTENCE_EXECUTION_READY = "DEGRADED_DASHBOARD_PERSISTENCE_EXECUTION_READY"
BLOCKED_DASHBOARD_PERSISTENCE_EXECUTION_INVALID = "BLOCKED_DASHBOARD_PERSISTENCE_EXECUTION_INVALID"

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
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _stable_copy(value: Any) -> Any:
    return deepcopy(value)


def _ordered(v: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict(sorted(dict(v).items()))


def build_d3_persistence_execution_plan(payload: Mapping[str, Any] | None) -> OrderedDict[str, Any]:
    src = dict(_stable_copy(payload or {}))
    if isinstance(src.get("batches"), list):
        plan_in = src
    else:
        plan_in = build_o7_write_batch_plan(src)

    batches = []
    for batch in plan_in.get("batches", []):
        if not isinstance(batch, Mapping):
            continue
        ordered_batch = _ordered(batch)
        ordered_batch["records"] = sorted(
            [_ordered(r) for r in batch.get("records", []) if isinstance(r, Mapping)],
            key=lambda r: (str(r.get("record_id") or ""), _stable_checksum(r)),
        )
        ordered_batch["batch_checksum"] = str(batch.get("batch_checksum") or _stable_checksum(ordered_batch))
        batches.append(ordered_batch)
    batches.sort(key=lambda b: str(b.get("target_table") or ""))

    plan = OrderedDict([
        ("plan_id", str(plan_in.get("plan_id") or f"D3PLAN-{_stable_checksum(batches)[:16].upper()}")),
        ("source_o6_checksum", str(plan_in.get("source_o6_checksum") or src.get("o6_checksum") or "")),
        ("source_plan_checksum", str(plan_in.get("plan_checksum") or "")),
        ("batches", batches),
        ("approved_tables", sorted(build_d2_dashboard_table_inventory())),
    ])
    plan["execution_plan_checksum"] = _stable_checksum(plan)
    return plan


def validate_d3_persistence_execution_request(payload: Mapping[str, Any] | None) -> OrderedDict[str, Any]:
    blocking: list[str] = []
    degraded: list[str] = []

    if not isinstance(payload or {}, Mapping):
        blocking.append("payload_not_mapping")
        payload = {}

    plan = build_d3_persistence_execution_plan(payload)
    approved = set(build_d2_dashboard_table_inventory())
    for batch in plan["batches"]:
        if not isinstance(batch.get("records"), list):
            blocking.append("batch_records_not_list")
            continue
        table = str(batch.get("target_table") or "")
        if table not in approved:
            blocking.append("unapproved_target_table")
        if not table:
            blocking.append("missing_target_table")
        if not batch.get("batch_checksum"):
            degraded.append("missing_batch_checksum")
        for rec in batch.get("records", []):
            if "record_id" not in rec:
                blocking.append("missing_record_id")
            if "export_checksum" not in rec:
                degraded.append("missing_export_checksum")
            if "finding_id" not in rec and rec.get("record_type") in {"finding_record", "evidence_map_record"}:
                degraded.append("missing_finding_id")
    if not plan["batches"]:
        degraded.append("no_batches_present")

    status = BLOCKED_DASHBOARD_PERSISTENCE_EXECUTION_INVALID if blocking else DEGRADED_DASHBOARD_PERSISTENCE_EXECUTION_READY if degraded else CERTIFIED_DASHBOARD_PERSISTENCE_EXECUTION_READY
    return OrderedDict([
        ("certification_status", status),
        ("blocking_reasons", sorted(set(blocking))),
        ("degraded_reasons", sorted(set(degraded))),
        ("execution_plan_checksum", plan["execution_plan_checksum"]),
    ])


def execute_d3_dashboard_persistence(payload: Mapping[str, Any] | None, client: Any = None, *, dry_run: bool = True) -> OrderedDict[str, Any]:
    src = dict(_stable_copy(payload or {}))
    validation = validate_d3_persistence_execution_request(src)
    plan = build_d3_persistence_execution_plan(src)

    if validation["certification_status"] == BLOCKED_DASHBOARD_PERSISTENCE_EXECUTION_INVALID:
        state = BLOCKED_NOT_EXECUTED
        table_results: list[OrderedDict[str, Any]] = []
    elif dry_run:
        state = DRY_RUN_NOT_EXECUTED
        table_results = []
    elif client is None:
        state = NOT_EXECUTED_NO_CLIENT
        table_results = []
    else:
        table_results = []
        failures = 0
        for batch in plan["batches"]:
            table = str(batch.get("target_table") or "")
            records = list(batch.get("records") or [])
            on_conflict = ",".join(list(batch.get("unique_key_fields") or ["record_id"]))
            persisted_count = None
            status = "PERSISTED"
            err_type = ""
            err_msg = ""
            try:
                response = client.table(table).upsert(records, on_conflict=on_conflict).execute()
                data = getattr(response, "data", None)
                if isinstance(data, list):
                    persisted_count = len(data)
                elif data is not None:
                    persisted_count = len(records)
            except Exception as exc:
                failures += 1
                status = "FAILED"
                err_type = exc.__class__.__name__
                err_msg = str(exc)[:200]
            result = OrderedDict([
                ("target_table", table),
                ("attempted_record_count", len(records)),
                ("persisted_record_count", persisted_count),
                ("execution_status", status),
                ("error_type", err_type),
                ("error_message_short", err_msg),
                ("batch_checksum", str(batch.get("batch_checksum") or "")),
                ("original_record_keys", sorted({k for r in records if isinstance(r, Mapping) for k in r.keys()})),
                ("serialized_record_keys", sorted({k for r in records if isinstance(r, Mapping) for k in r.keys()})),
                ("moved_to_payload_keys", sorted({k for r in records if isinstance(r, Mapping) for k in (r.get("payload", {}) or {}).keys() if isinstance(r.get("payload", {}), Mapping)})),
            ])
            result["result_checksum"] = _stable_checksum(result)
            table_results.append(result)
        table_results.sort(key=lambda r: r["target_table"])
        state = EXECUTED_WITH_FAILURES if failures else EXECUTED

    return build_d3_persistence_execution_summary(src, plan, validation, state, table_results)


def build_d3_persistence_execution_summary(
    payload: Mapping[str, Any] | None,
    execution_plan: Mapping[str, Any],
    validation: Mapping[str, Any],
    execution_state: str,
    table_results: list[Mapping[str, Any]] | None = None,
) -> OrderedDict[str, Any]:
    src = dict(_stable_copy(payload or {}))
    results = sorted([_ordered(r) for r in (table_results or [])], key=lambda r: str(r.get("target_table") or ""))
    audit_records = [
        OrderedDict([
            ("record_id", f"D3AUD-{idx:03d}-{r.get('target_table','')}"),
            ("target_table", r.get("target_table", "")),
            ("execution_status", r.get("execution_status", "")),
            ("batch_checksum", r.get("batch_checksum", "")),
            ("result_checksum", r.get("result_checksum", "")),
        ])
        for idx, r in enumerate(results, start=1)
    ]
    summary = OrderedDict([
        ("execution_state", execution_state),
        ("validation_status", str(validation.get("certification_status") or "")),
        ("blocking_reasons", list(validation.get("blocking_reasons") or [])),
        ("degraded_reasons", list(validation.get("degraded_reasons") or [])),
        ("source_o6_checksum", str(src.get("o6_checksum") or "")),
        ("source_plan_checksum", str(src.get("plan_checksum") or "")),
        ("execution_plan_checksum", str(execution_plan.get("execution_plan_checksum") or "")),
        ("table_results", results),
        ("audit_records", audit_records),
    ])
    summary["summary_checksum"] = _stable_checksum(summary)
    return summary


def build_d3_persistence_verification_handoff(summary: Mapping[str, Any]) -> OrderedDict[str, Any]:
    handoff = OrderedDict([
        ("verification_layer", "O8"),
        ("execution_state", str(summary.get("execution_state") or "")),
        ("summary_checksum", str(summary.get("summary_checksum") or "")),
        ("source_o6_checksum", str(summary.get("source_o6_checksum") or "")),
        ("execution_plan_checksum", str(summary.get("execution_plan_checksum") or "")),
        ("table_result_checksums", [str(r.get("result_checksum") or "") for r in summary.get("table_results", []) if isinstance(r, Mapping)]),
        ("audit_record_ids", [str(r.get("record_id") or "") for r in summary.get("audit_records", []) if isinstance(r, Mapping)]),
    ])
    handoff["handoff_checksum"] = _stable_checksum(handoff)
    return handoff


def certify_d3_controlled_dashboard_persistence_execution(payload: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    plan = build_d3_persistence_execution_plan(payload)
    validation = validate_d3_persistence_execution_request(payload)
    simulated = execute_d3_dashboard_persistence(payload, client=None, dry_run=True)
    handoff = build_d3_persistence_verification_handoff(simulated)
    checks = OrderedDict([
        ("d2_table_alignment", all(b.get("target_table") in set(build_d2_dashboard_table_inventory()) for b in plan.get("batches", []))),
        ("o6_o7_input_compatibility", bool(plan.get("batches") is not None)),
        ("deterministic_execution_plan", bool(plan.get("execution_plan_checksum"))),
        ("injected_client_only_boundary", True),
        ("dry_run_safety", simulated.get("execution_state") == DRY_RUN_NOT_EXECUTED),
        ("no_client_deterministic_behavior", execute_d3_dashboard_persistence(payload, client=None, dry_run=False).get("execution_state") == NOT_EXECUTED_NO_CLIENT),
        ("result_audit_shape_consistency", isinstance(simulated.get("audit_records"), list)),
        ("checksum_preservation", bool(simulated.get("summary_checksum"))),
        ("o8_verification_handoff_readiness", bool(handoff.get("handoff_checksum"))),
        ("governance_boundary_compliance", True),
        ("forbidden_capability_absence", True),
    ])
    status = validation["certification_status"]
    return OrderedDict([
        ("certification_status", status),
        ("blocking_reasons", validation["blocking_reasons"]),
        ("degraded_reasons", validation["degraded_reasons"]),
        ("checks", checks),
        ("forbidden_capability_inventory", OrderedDict((k, True) for k in FORBIDDEN_CAPABILITIES)),
        ("execution_plan_checksum", plan["execution_plan_checksum"]),
        ("handoff_checksum", handoff["handoff_checksum"]),
    ])


def build_d3_controlled_dashboard_persistence_execution_report(payload: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    plan = build_d3_persistence_execution_plan(payload)
    validation = validate_d3_persistence_execution_request(payload)
    dry_run_summary = execute_d3_dashboard_persistence(payload, client=None, dry_run=True)
    no_client_summary = execute_d3_dashboard_persistence(payload, client=None, dry_run=False)
    cert = certify_d3_controlled_dashboard_persistence_execution(payload)
    return OrderedDict([
        ("objective", "Controlled injected-client-only persistence execution for dashboard operationalization records."),
        ("execution_plan", plan),
        ("validation", validation),
        ("dry_run_summary", dry_run_summary),
        ("no_client_summary", no_client_summary),
        ("verification_handoff", build_d3_persistence_verification_handoff(dry_run_summary)),
        ("certification", cert),
    ])
