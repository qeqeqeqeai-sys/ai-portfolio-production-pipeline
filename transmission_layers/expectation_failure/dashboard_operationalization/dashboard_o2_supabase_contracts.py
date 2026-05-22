"""Deterministic Dashboard O2 Supabase persistence contracts and validations."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Any, Dict, Mapping, MutableMapping, Sequence

SCHEMA_VERSION = "dashboard_o2_supabase_contracts_v1"
MODULE_VERSION = "1.0.0"
PERSISTENCE_MODE = "upsert_contract_only"

TABLE_CONFIG = (
    ("expectation_failure_dashboard_entity_facts", "dashboard_entity_facts", ("run_id", "entity_id")),
    ("expectation_failure_dashboard_subsector_facts", "dashboard_subsector_facts", ("run_id", "subsector")),
    ("expectation_failure_dashboard_alert_facts", "dashboard_alert_facts", ("run_id", "entity_id", "alert_state")),
    ("expectation_failure_dashboard_replay_facts", "dashboard_replay_facts", ("run_id", "replay_date_sgt", "entity_id", "replay_sequence")),
    ("expectation_failure_dashboard_benchmark_facts", "dashboard_benchmark_facts", ("run_id", "entity_id", "benchmark_id")),
    ("expectation_failure_dashboard_evidence_facts", "dashboard_evidence_facts", ("run_id", "entity_id", "evidence_id")),
    ("expectation_failure_dashboard_report_metadata", "dashboard_report_metadata", ("run_id", "report_id")),
    ("expectation_failure_dashboard_export_manifest", "dashboard_export_manifest", ("run_id", "checksum")),
)

FORBIDDEN_TERMS = (
    "buy", "sell", "short", "target price", "portfolio allocation", "backtesting", "predictive", "recommendation", "trade"
)


def _stable_checksum(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _is_flat_dict(row: Mapping[str, Any]) -> bool:
    for value in row.values():
        if isinstance(value, (dict, list, tuple, set)):
            return False
    return True


def build_dashboard_o2_table_contracts() -> list[OrderedDict]:
    contracts = []
    for table_name, source_payload_key, primary_unique_key in TABLE_CONFIG:
        contracts.append(OrderedDict([
            ("table_name", table_name),
            ("source_payload_key", source_payload_key),
            ("primary_unique_key", list(primary_unique_key)),
            ("columns", []),
            ("required_columns", list(primary_unique_key)),
            ("nullable_columns", []),
            ("deterministic_sort_key", list(primary_unique_key)),
            ("persistence_mode", PERSISTENCE_MODE),
            ("schema_version", SCHEMA_VERSION),
        ]))
    return contracts


def build_dashboard_o2_unique_key_contracts() -> OrderedDict:
    return OrderedDict((t, list(u)) for t, _, u in TABLE_CONFIG)


def build_dashboard_o2_column_contracts(payload: Mapping[str, Any]) -> OrderedDict:
    materialized = deepcopy(dict(payload))
    column_contracts: MutableMapping[str, list[str]] = OrderedDict()
    for table_name, source_key, unique_key in TABLE_CONFIG:
        rows = materialized.get(source_key)
        if isinstance(rows, Mapping):
            rows = [rows]
        rows = list(rows or [])
        columns: list[str] = []
        if rows:
            first = rows[0]
            if isinstance(first, Mapping):
                columns = list(first.keys())
        for key in unique_key:
            if key not in columns:
                columns.append(key)
        column_contracts[table_name] = columns
    return OrderedDict(column_contracts)


def validate_dashboard_o2_payload(payload: Mapping[str, Any]) -> OrderedDict:
    materialized = deepcopy(dict(payload))
    errors: list[str] = []
    table_contracts = build_dashboard_o2_table_contracts()
    column_contracts = build_dashboard_o2_column_contracts(materialized)
    seen_keys: Dict[str, set[tuple[Any, ...]]] = {}

    for contract in table_contracts:
        table_name = contract["table_name"]
        source_key = contract["source_payload_key"]
        unique_key = contract["primary_unique_key"]

        if source_key not in materialized:
            errors.append(f"missing payload group: {source_key}")
            continue

        group = materialized[source_key]
        if isinstance(group, Mapping):
            rows = [group]
        elif isinstance(group, list):
            rows = group
        else:
            errors.append(f"invalid payload group type for {source_key}")
            continue

        required_cols = unique_key
        table_cols = column_contracts[table_name]
        for col in required_cols:
            if col not in table_cols:
                errors.append(f"missing required column {col} in {source_key}")

        seen_keys[table_name] = set()
        for idx, row in enumerate(rows):
            if not isinstance(row, Mapping):
                errors.append(f"row {idx} in {source_key} is not dict")
                continue
            if source_key != "dashboard_export_manifest" and not _is_flat_dict(row):
                errors.append(f"row {idx} in {source_key} is not flat")
            for col in required_cols:
                if col not in row:
                    errors.append(f"row {idx} missing required column {col} in {source_key}")
            key_tuple = tuple(row.get(k) for k in unique_key)
            if any(v is None for v in key_tuple):
                errors.append(f"row {idx} has null unique key in {source_key}")
            if key_tuple in seen_keys[table_name]:
                errors.append(f"duplicate unique key in {source_key}: {key_tuple}")
            seen_keys[table_name].add(key_tuple)
            for value in row.values():
                if isinstance(value, str):
                    low = value.lower()
                    if any(term in low for term in FORBIDDEN_TERMS):
                        errors.append(f"forbidden term detected in {source_key}")
                        break

    validation_status = "valid" if not errors else "invalid"
    return OrderedDict([
        ("validation_status", validation_status),
        ("error_count", len(errors)),
        ("errors", errors),
        ("deterministic_table_order", [c["source_payload_key"] for c in table_contracts]),
    ])


def build_dashboard_o2_persistence_manifest(*, table_contracts: Sequence[Mapping[str, Any]], upsert_batches: Sequence[Mapping[str, Any]], validation_summary: Mapping[str, Any]) -> OrderedDict:
    table_row_counts = OrderedDict((batch["table_name"], int(batch["row_count"])) for batch in upsert_batches)
    total_rows = sum(table_row_counts.values())
    manifest_payload = OrderedDict([
        ("schema_version", SCHEMA_VERSION),
        ("module_version", MODULE_VERSION),
        ("table_count", len(table_contracts)),
        ("total_row_count", total_rows),
        ("table_row_counts", table_row_counts),
        ("deterministic_table_order", [batch["table_name"] for batch in upsert_batches]),
        ("persistence_mode", PERSISTENCE_MODE),
        ("validation_status", validation_summary.get("validation_status", "invalid")),
        ("invariant_flags", OrderedDict([
            ("deterministic_only", True),
            ("contract_only", True),
            ("no_database_writes", True),
            ("no_network_calls", True),
            ("no_file_writes", True),
            ("no_streamlit_ui", True),
            ("no_trading_recommendations", True),
            ("immutable_input_safe", True),
        ])),
    ])
    manifest_payload["checksum"] = _stable_checksum(manifest_payload)
    return manifest_payload


def build_dashboard_o2_upsert_payload(payload: Mapping[str, Any]) -> OrderedDict:
    materialized = deepcopy(dict(payload))
    table_contracts = build_dashboard_o2_table_contracts()
    column_contracts = build_dashboard_o2_column_contracts(materialized)
    for contract in table_contracts:
        table = contract["table_name"]
        columns = column_contracts[table]
        contract["columns"] = columns
        contract["required_columns"] = list(contract["primary_unique_key"])
        contract["nullable_columns"] = [c for c in columns if c not in contract["required_columns"]]

    upsert_batches = []
    for contract in table_contracts:
        source_key = contract["source_payload_key"]
        group = materialized.get(source_key, [])
        if isinstance(group, Mapping):
            rows = [group]
        else:
            rows = list(group or [])
        ordered = sorted(rows, key=lambda r: tuple(r.get(k) for k in contract["deterministic_sort_key"])) if rows else []
        upsert_batches.append(OrderedDict([
            ("table_name", contract["table_name"]),
            ("source_payload_key", source_key),
            ("unique_key", list(contract["primary_unique_key"])),
            ("rows", ordered),
            ("row_count", len(ordered)),
            ("deterministic_sort_key", list(contract["deterministic_sort_key"])),
            ("persistence_mode", PERSISTENCE_MODE),
        ]))

    validation_summary = validate_dashboard_o2_payload(materialized)
    persistence_manifest = build_dashboard_o2_persistence_manifest(
        table_contracts=table_contracts,
        upsert_batches=upsert_batches,
        validation_summary=validation_summary,
    )
    return OrderedDict([
        ("table_contracts", table_contracts),
        ("upsert_batches", upsert_batches),
        ("validation_summary", validation_summary),
        ("persistence_manifest", persistence_manifest),
    ])


def build_dashboard_o2_contract_report(payload: Mapping[str, Any]) -> OrderedDict:
    built = build_dashboard_o2_upsert_payload(payload)
    return OrderedDict([
        ("table_contracts", built["table_contracts"]),
        ("unique_key_contracts", build_dashboard_o2_unique_key_contracts()),
        ("column_contracts", build_dashboard_o2_column_contracts(payload)),
        ("validation_summary", built["validation_summary"]),
        ("persistence_manifest", built["persistence_manifest"]),
    ])


__all__ = [
    "build_dashboard_o2_table_contracts",
    "build_dashboard_o2_unique_key_contracts",
    "build_dashboard_o2_column_contracts",
    "build_dashboard_o2_upsert_payload",
    "validate_dashboard_o2_payload",
    "build_dashboard_o2_persistence_manifest",
    "build_dashboard_o2_contract_report",
]
