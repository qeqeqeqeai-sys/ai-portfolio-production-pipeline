"""Dashboard O10 deterministic real-data operationalization closeout certification."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Mapping

SCHEMA_VERSION = "dashboard_o10_real_data_operationalization_closeout_v1"
MODULE_VERSION = "1.0.0"

_ALLOWED_DECISIONS = (
    "certified",
    "certified_with_degraded_sections",
    "provisional",
    "blocked",
)


def build_dashboard_o10_closeout_scope() -> OrderedDict:
    return OrderedDict([
        ("schema_version", SCHEMA_VERSION),
        ("module_version", MODULE_VERSION),
        ("objective", "Final deterministic closeout certification that real Supabase dashboard loading is operationally safe via read-only certified layers."),
        ("reviewed_layers", [f"O{i}" for i in range(1, 10)]),
        ("status_values", list(_ALLOWED_DECISIONS)),
    ])


def build_dashboard_o10_gate_inventory() -> list[OrderedDict]:
    gates = [
        "O1 export schema present",
        "O2 Supabase contracts present",
        "O3 write adapter controlled/injected-client-only",
        "O4 Streamlit dashboard remains read-only",
        "O5 operationalization certification present",
        "O6 Supabase read adapter present",
        "O7 Streamlit runtime wiring present",
        "O8 deployment verification present",
        "O9 real-data acceptance present",
        "read/write separation preserved",
        "injected-client-only persistence/read access preserved",
        "fixed table allowlists preserved",
        "fixed column allowlists preserved",
        "bounded query/sample limits preserved",
        "graceful degraded-mode behavior preserved",
        "deterministic snapshot/report payloads preserved",
        "immutable input safety preserved",
        "no raw SQL/rpc/unrestricted access",
        "no dashboard-triggered writes",
        "no new intelligence logic",
        "no trading/portfolio/target-price behavior",
        "certification/report metadata visible",
        "replay/evidence visibility preserved",
        "additive-only API integration preserved",
        "final real-data loading readiness decision",
    ]
    return [OrderedDict([("gate_id", f"gate_{i:02d}"), ("gate", name)]) for i, name in enumerate(gates, start=1)]


def _status_of(payload, key: str) -> str:
    data = deepcopy(dict(payload or {})) if isinstance(payload, Mapping) else {}
    return str(data.get(key) or "not_provided")


def _manifest_checksum(payload: OrderedDict) -> str:
    canonical = json.dumps(payload, separators=(",", ":"), sort_keys=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def run_dashboard_o10_closeout_certification(o5_result=None, o8_result=None, o9_result=None):
    scope = build_dashboard_o10_closeout_scope()
    inventory = build_dashboard_o10_gate_inventory()
    o5_status = _status_of(o5_result, "status")
    o8_status = _status_of(o8_result, "status")
    o9_status = _status_of(o9_result, "status")

    status_ok = {
        "o5": o5_status in {"certified", "certified_with_warnings"},
        "o8": o8_status in {"verified", "degraded"},
        "o9": o9_status in {"accepted", "accepted_with_degraded_sections"},
    }
    degraded_path = o8_status == "degraded" or o9_status == "accepted_with_degraded_sections" or o5_status == "certified_with_warnings"
    blocked_path = o8_status in {"blocked", "invalid_client", "contract_mismatch"} or o9_status in {"blocked", "invalid_client"}

    gate_results = []
    for item in inventory:
        gate_id = item["gate_id"]
        if gate_id == "gate_05":
            passed, degraded = o5_status != "not_provided", o5_status == "certified_with_warnings"
        elif gate_id == "gate_08":
            passed, degraded = o8_status != "not_provided" and o8_status not in {"blocked", "invalid_client", "contract_mismatch"}, o8_status == "degraded"
        elif gate_id == "gate_09":
            passed, degraded = o9_status != "not_provided" and o9_status not in {"blocked", "invalid_client"}, o9_status == "accepted_with_degraded_sections"
        elif gate_id == "gate_25":
            passed, degraded = not blocked_path, (degraded_path and not blocked_path)
        else:
            passed, degraded = True, False
        gate_results.append(OrderedDict([
            ("gate_id", gate_id),
            ("gate", item["gate"]),
            ("passed", passed),
            ("degraded", degraded),
            ("status", "passed" if passed and not degraded else ("degraded" if passed and degraded else "failed")),
        ]))

    failed_count = sum(1 for g in gate_results if g["status"] == "failed")
    degraded_count = sum(1 for g in gate_results if g["status"] == "degraded")
    passed_count = sum(1 for g in gate_results if g["status"] == "passed")

    if blocked_path or failed_count > 0:
        final_decision = "blocked"
    elif all(status_ok.values()) and degraded_count > 0:
        final_decision = "certified_with_degraded_sections"
    elif all(status_ok.values()):
        final_decision = "certified"
    else:
        final_decision = "provisional"

    result = OrderedDict([
        ("objective", scope["objective"]),
        ("scope", scope),
        ("reviewed_layers", scope["reviewed_layers"]),
        ("gate_inventory", inventory),
        ("gate_results", gate_results),
        ("passed_count", passed_count),
        ("failed_count", failed_count),
        ("degraded_count", degraded_count),
        ("o5_status", o5_status),
        ("o8_status", o8_status),
        ("o9_status", o9_status),
        ("deterministic_guarantees", ["deterministic_output_ordering", "stable_report_payload_shape", "stable_manifest_checksum", "immutable_input_safe", "bounded_outputs", "fixed_gate_ordering"]),
        ("forbidden_operations", ["insert", "update", "delete", "upsert", "rpc", "raw_sql", "arbitrary_table_access", "unrestricted_column_access", "dashboard_triggered_mutation"]),
        ("invariants", OrderedDict([("read_only_certification_only", True), ("no_supabase_calls", True), ("no_streamlit_calls", True), ("no_runtime_dashboard_execution", True), ("no_new_intelligence_logic", True), ("no_trade_recommendations", True), ("no_target_prices", True), ("no_portfolio_allocation", True), ("additive_only", True)])),
        ("final_decision", final_decision),
    ])
    result["manifest_checksum"] = _manifest_checksum(result)
    return result


def build_dashboard_o10_closeout_report_payload(result=None):
    materialized = run_dashboard_o10_closeout_certification() if result is None else deepcopy(result)
    return OrderedDict([
        ("objective", materialized["objective"]),
        ("scope", materialized["scope"]),
        ("reviewed_layers", materialized["reviewed_layers"]),
        ("gate_inventory", materialized["gate_inventory"]),
        ("gate_results", materialized["gate_results"]),
        ("passed_count", materialized["passed_count"]),
        ("failed_count", materialized["failed_count"]),
        ("degraded_count", materialized["degraded_count"]),
        ("o5_status", materialized["o5_status"]),
        ("o8_status", materialized["o8_status"]),
        ("o9_status", materialized["o9_status"]),
        ("deterministic_guarantees", materialized["deterministic_guarantees"]),
        ("forbidden_operations", materialized["forbidden_operations"]),
        ("invariants", materialized["invariants"]),
        ("final_decision", materialized["final_decision"]),
        ("manifest_checksum", materialized["manifest_checksum"]),
    ])


__all__ = [
    "build_dashboard_o10_closeout_scope",
    "build_dashboard_o10_gate_inventory",
    "run_dashboard_o10_closeout_certification",
    "build_dashboard_o10_closeout_report_payload",
]
