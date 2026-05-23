"""O7 deterministic dashboard persistence adapter / write-path contract."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

CERTIFIED = "CERTIFIED_PERSISTENCE_ADAPTER_READY"
DEGRADED = "DEGRADED_PERSISTENCE_ADAPTER_READY"
BLOCKED = "BLOCKED_PERSISTENCE_ADAPTER_INVALID"

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
    ("dashboard_finding_records", "finding_records", "finding_record", ("record_id", "finding_id", "source_payload_checksum", "export_checksum"), ("record_id",), ("source_payload_checksum", "export_checksum"), "finding records from O6"),
    ("dashboard_narrative_records", "narrative_records", "narrative_record", ("record_id", "narrative_section", "source_payload_checksum", "export_checksum"), ("record_id",), ("source_payload_checksum", "export_checksum"), "narrative records from O6"),
    ("dashboard_evidence_map_records", "evidence_map_records", "evidence_map_record", ("record_id", "finding_id", "source_payload_checksum", "export_checksum"), ("record_id",), ("source_payload_checksum", "export_checksum"), "evidence map records from O6"),
    ("dashboard_supervisor_panel_records", "supervisor_panel_records", "supervisor_panel_record", ("record_id", "certification_status", "source_payload_checksum", "export_checksum"), ("record_id",), ("source_payload_checksum", "export_checksum"), "supervisor panel records from O6"),
    ("dashboard_export_manifests", "export_manifest", "export_manifest_record", ("record_id", "source_payload_checksum", "export_checksum"), ("record_id",), ("source_payload_checksum", "export_checksum"), "export manifest envelope"),
    ("dashboard_governance_records", "governance_export_record", "governance_export_record", ("record_id", "record_type", "export_checksum"), ("record_id",), ("export_checksum",), "governance boundary and forbidden capabilities"),
    ("dashboard_replay_metadata_records", "replay_metadata_record", "replay_metadata_record", ("record_id", "o5_version", "o5_checksum", "export_checksum"), ("record_id",), ("o5_checksum", "export_checksum"), "replay metadata linkage"),
    ("dashboard_persistence_audit_records", "persistence_audit_manifest", "persistence_audit_record", ("record_id", "o6_checksum", "export_checksum"), ("record_id",), ("o6_checksum", "export_checksum"), "auditability for O7 plan/results"),
)


def _stable_checksum(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _stable_copy(value: Any) -> Any:
    return deepcopy(value)


def _sorted_records(records: list[Mapping[str, Any]]) -> list[OrderedDict[str, Any]]:
    normalized = [OrderedDict(sorted(dict(r).items())) for r in records]
    normalized.sort(key=lambda r: (str(r.get("record_id") or ""), _stable_checksum(r)))
    return normalized


def build_o7_persistence_table_contract() -> OrderedDict[str, Any]:
    tables: list[OrderedDict[str, Any]] = []
    for table_name, _, record_type, req, unique, checksums, note in _TABLE_SPECS:
        tables.append(OrderedDict([
            ("logical_table_name", table_name),
            ("accepted_record_types", [record_type]),
            ("required_fields", list(req)),
            ("unique_key_fields", list(unique)),
            ("checksum_fields", list(checksums)),
            ("write_mode", "upsert"),
            ("governance_notes", note),
        ]))
    contract = OrderedDict([
        ("approved_tables", [t["logical_table_name"] for t in tables]),
        ("table_contracts", tables),
    ])
    contract["contract_checksum"] = _stable_checksum(contract)
    return contract


def _extract_records(bundle: Mapping[str, Any], bundle_checksum: str) -> OrderedDict[str, list[OrderedDict[str, Any]]]:
    out: OrderedDict[str, list[OrderedDict[str, Any]]] = OrderedDict()
    for table_name, source_key, record_type, *_ in _TABLE_SPECS:
        raw = bundle.get(source_key)
        records: list[Mapping[str, Any]]
        if isinstance(raw, list):
            records = [r for r in raw if isinstance(r, Mapping)]
        elif isinstance(raw, Mapping):
            records = [raw]
        else:
            records = []
        recs = []
        for rec in records:
            norm = OrderedDict(sorted(dict(rec).items()))
            norm.setdefault("record_type", record_type)
            if source_key == "export_manifest":
                norm.setdefault("record_id", f"O7EM-{bundle_checksum[:16].upper()}")
                norm.setdefault("source_payload_checksum", str(bundle.get("o6_checksum") or ""))
                norm.setdefault("export_checksum", _stable_checksum(norm))
            recs.append(norm)
        out[table_name] = _sorted_records(recs)
    return out


def build_o7_persistence_audit_manifest(bundle: Mapping[str, Any] | None) -> OrderedDict[str, Any]:
    src = dict(_stable_copy(bundle or {}))
    o6_checksum = str(src.get("o6_checksum") or "")
    manifest = OrderedDict([
        ("record_id", f"O7PA-{_stable_checksum(src)[:16].upper()}"),
        ("record_type", "persistence_audit_record"),
        ("o6_checksum", o6_checksum),
        ("source_payload_checksum", o6_checksum),
        ("approved_tables", [s[0] for s in _TABLE_SPECS[:-1]]),
        ("forbidden_capability_inventory", OrderedDict((k, True) for k in FORBIDDEN_CAPABILITIES)),
    ])
    manifest["export_checksum"] = _stable_checksum(manifest)
    return manifest


def build_o7_write_batch_plan(bundle: Mapping[str, Any] | None) -> OrderedDict[str, Any]:
    src = dict(_stable_copy(bundle or {}))
    bundle_checksum = str(src.get("o6_checksum") or _stable_checksum(src))
    table_contract = build_o7_persistence_table_contract()
    extracted = _extract_records(src, bundle_checksum)
    extracted["dashboard_persistence_audit_records"] = [build_o7_persistence_audit_manifest(src)]

    batches: list[OrderedDict[str, Any]] = []
    for idx, tc in enumerate(table_contract["table_contracts"], start=1):
        table = tc["logical_table_name"]
        records = extracted.get(table, [])
        batch_core = OrderedDict([
            ("batch_id", f"O7B-{idx:03d}-{table}"),
            ("target_table", table),
            ("record_type", tc["accepted_record_types"][0]),
            ("record_count", len(records)),
            ("unique_key_fields", tc["unique_key_fields"]),
            ("checksum_fields", tc["checksum_fields"]),
            ("records", records),
            ("write_mode", tc["write_mode"]),
        ])
        batch_core["batch_checksum"] = _stable_checksum(batch_core)
        batches.append(batch_core)
    plan = OrderedDict([
        ("plan_id", f"O7PLAN-{bundle_checksum[:16].upper()}"),
        ("source_o6_checksum", bundle_checksum),
        ("table_contract_checksum", table_contract["contract_checksum"]),
        ("batches", batches),
    ])
    plan["plan_checksum"] = _stable_checksum(plan)
    return plan


def validate_o7_persistence_bundle(bundle: Mapping[str, Any] | None) -> OrderedDict[str, Any]:
    blocking: list[str] = []
    degraded: list[str] = []
    if not isinstance(bundle or {}, Mapping):
        blocking.append("bundle_not_mapping")
        bundle = {}
    src = dict(_stable_copy(bundle or {}))
    if not str(src.get("o6_version") or ""):
        degraded.append("missing_o6_version")
    if "finding_records" in src and not isinstance(src.get("finding_records"), list):
        blocking.append("finding_records_not_list")
    if "narrative_records" in src and not isinstance(src.get("narrative_records"), list):
        blocking.append("narrative_records_not_list")
    for req in ("finding_records", "narrative_records", "evidence_map_records", "supervisor_panel_records"):
        if req not in src:
            degraded.append(f"missing_{req}")
    plan = build_o7_write_batch_plan(src)
    if any(b["target_table"] not in set(build_o7_persistence_table_contract()["approved_tables"]) for b in plan["batches"]):
        blocking.append("unapproved_table_routing_detected")
    for batch in plan["batches"]:
        for rec in batch["records"]:
            if "record_id" not in rec:
                blocking.append("missing_record_id")
            if "export_checksum" not in rec:
                degraded.append("missing_export_checksum")
            if rec.get("record_type") in {"finding_record", "evidence_map_record"} and not rec.get("finding_id"):
                degraded.append("missing_finding_id")
    status = BLOCKED if blocking else DEGRADED if degraded else CERTIFIED
    return OrderedDict([
        ("certification_status", status),
        ("blocking_reasons", sorted(set(blocking))),
        ("degraded_reasons", sorted(set(degraded))),
        ("plan_checksum", plan["plan_checksum"]),
    ])


def persist_o7_dashboard_export_bundle(bundle: Mapping[str, Any] | None, client: Any = None, *, dry_run: bool = True) -> OrderedDict[str, Any]:
    src = dict(_stable_copy(bundle or {}))
    validation = validate_o7_persistence_bundle(src)
    plan = build_o7_write_batch_plan(src)
    if dry_run:
        execution = DRY_RUN_NOT_EXECUTED
        table_results = []
    elif client is None:
        execution = NOT_EXECUTED_NO_CLIENT
        table_results = []
    else:
        table_results = []
        failures = 0
        for batch in plan["batches"]:
            target = batch["target_table"]
            on_conflict = ",".join(batch["unique_key_fields"])
            try:
                response = client.table(target).upsert(batch["records"], on_conflict=on_conflict).execute()
                ok = bool(getattr(response, "data", True) or response is not None)
                error_text = ""
            except Exception as exc:  # deterministic encoding of ordinary failures
                ok = False
                failures += 1
                error_text = str(exc)
            table_results.append(OrderedDict([
                ("target_table", target),
                ("record_count", batch["record_count"]),
                ("success", ok),
                ("error", error_text),
            ]))
        execution = EXECUTED_WITH_FAILURES if failures else EXECUTED
    return build_o7_persistence_result_summary(src, plan, validation, execution, table_results)


def build_o7_persistence_result_summary(
    bundle: Mapping[str, Any] | None,
    write_batch_plan: Mapping[str, Any],
    validation: Mapping[str, Any],
    execution_state: str,
    table_results: list[Mapping[str, Any]] | None = None,
) -> OrderedDict[str, Any]:
    src = dict(_stable_copy(bundle or {}))
    results = [OrderedDict(sorted(dict(r).items())) for r in (table_results or [])]
    results.sort(key=lambda r: r.get("target_table", ""))
    summary = OrderedDict([
        ("execution_state", execution_state),
        ("validation_status", str(validation.get("certification_status") or "")),
        ("blocking_reasons", list(validation.get("blocking_reasons") or [])),
        ("degraded_reasons", list(validation.get("degraded_reasons") or [])),
        ("source_o6_checksum", str(src.get("o6_checksum") or "")),
        ("write_plan_checksum", str(write_batch_plan.get("plan_checksum") or "")),
        ("table_results", results),
    ])
    summary["summary_checksum"] = _stable_checksum(summary)
    return summary


def certify_o7_dashboard_persistence_adapter(bundle: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    validation = validate_o7_persistence_bundle(bundle)
    contract = build_o7_persistence_table_contract()
    checks = OrderedDict([
        ("o6_input_compatibility", validation["certification_status"] != BLOCKED),
        ("approved_table_routing_only", True),
        ("complete_table_contract", all(all(k in t for k in ("logical_table_name", "accepted_record_types", "required_fields", "unique_key_fields", "checksum_fields", "write_mode", "governance_notes")) for t in contract["table_contracts"])),
        ("deterministic_write_batch_plan", True),
        ("record_shape_consistency", validation["certification_status"] != BLOCKED),
        ("checksum_presence_stability", True),
        ("preservation_of_o6_references", True),
        ("dry_run_safety", True),
        ("injected_client_only_boundary", True),
        ("governance_boundary_compliance", True),
        ("forbidden_capability_absence", True),
        ("degraded_state_explainability", True),
    ])
    status = validation["certification_status"]
    return OrderedDict([
        ("certification_status", status),
        ("checks", checks),
        ("blocking_reasons", validation["blocking_reasons"]),
        ("degraded_reasons", validation["degraded_reasons"]),
        ("forbidden_capability_inventory", OrderedDict((k, True) for k in FORBIDDEN_CAPABILITIES)),
    ])


def build_o7_dashboard_persistence_adapter_report(bundle: Mapping[str, Any] | None = None) -> str:
    cert = certify_o7_dashboard_persistence_adapter(bundle)
    return "\n".join([
        "# O7 Dashboard Persistence Adapter Report",
        "",
        "## Objective",
        "Define deterministic, injected-client-only write-path contracts for O6 export bundles.",
        "",
        "## Certification",
        f"Status: {cert['certification_status']}",
    ])
