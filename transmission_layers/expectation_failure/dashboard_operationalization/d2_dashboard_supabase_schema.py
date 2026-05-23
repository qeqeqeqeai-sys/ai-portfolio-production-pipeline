"""D2 dashboard Supabase schema contract and certification utilities."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

CERTIFIED_DASHBOARD_SCHEMA_READY = "CERTIFIED_DASHBOARD_SCHEMA_READY"
DEGRADED_DASHBOARD_SCHEMA_READY = "DEGRADED_DASHBOARD_SCHEMA_READY"
BLOCKED_DASHBOARD_SCHEMA_INVALID = "BLOCKED_DASHBOARD_SCHEMA_INVALID"

MIGRATION_PATH = "supabase/migrations/20260524000100_create_dashboard_operationalization_tables.sql"

_REQUIRED_TABLES: List[str] = [
    "dashboard_finding_records",
    "dashboard_narrative_records",
    "dashboard_evidence_map_records",
    "dashboard_supervisor_panel_records",
    "dashboard_export_manifests",
    "dashboard_governance_records",
    "dashboard_replay_metadata_records",
    "dashboard_persistence_audit_records",
]


def build_d2_dashboard_table_inventory() -> List[str]:
    return list(_REQUIRED_TABLES)


def build_d2_dashboard_column_contract() -> Dict[str, List[str]]:
    common = [
        "record_id",
        "record_type",
        "source_payload_checksum",
        "export_checksum",
        "created_at",
        "updated_at",
        "payload",
        "lineage_refs",
        "evidence_refs",
        "governance_notes",
        "replay_metadata",
    ]
    return {
        "dashboard_finding_records": common + ["finding_id", "finding_type", "finding_title", "finding_severity", "finding_direction", "confidence_label"],
        "dashboard_narrative_records": common + ["narrative_section", "related_finding_ids"],
        "dashboard_evidence_map_records": common + ["finding_id", "evidence_ref"],
        "dashboard_supervisor_panel_records": common + ["panel_name", "panel_status"],
        "dashboard_export_manifests": common + ["manifest_id", "manifest_checksum"],
        "dashboard_governance_records": common + ["governance_status", "forbidden_capabilities"],
        "dashboard_replay_metadata_records": common + ["replay_id", "replay_checksum"],
        "dashboard_persistence_audit_records": common + ["audit_id", "batch_id", "target_table", "write_status"],
    }


def build_d2_dashboard_index_contract() -> Dict[str, List[str]]:
    contract: Dict[str, List[str]] = {}
    for table in _REQUIRED_TABLES:
        contract[table] = ["record_type", "source_payload_checksum", "export_checksum", "payload_gin", "lineage_refs_gin", "evidence_refs_gin"]
    contract["dashboard_finding_records"] += ["finding_id", "finding_severity", "confidence_label"]
    contract["dashboard_narrative_records"] += ["narrative_section"]
    contract["dashboard_persistence_audit_records"] += ["batch_id", "target_table", "write_status"]
    return contract


def build_d2_dashboard_constraint_contract() -> Dict[str, Dict[str, List[str]]]:
    return {
        table: {
            "primary_key": ["record_id"],
            "not_null": ["record_id", "record_type", "created_at", "updated_at", "payload", "lineage_refs", "evidence_refs", "governance_notes", "replay_metadata"],
            "checks": [],
        }
        for table in _REQUIRED_TABLES
    }


def _canonical_checksum(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_d2_dashboard_supabase_schema_contract() -> Dict[str, Any]:
    contract = {
        "layer": "D2",
        "migration_path": MIGRATION_PATH,
        "table_inventory": build_d2_dashboard_table_inventory(),
        "column_contract": build_d2_dashboard_column_contract(),
        "index_contract": build_d2_dashboard_index_contract(),
        "constraint_contract": build_d2_dashboard_constraint_contract(),
        "required_checksum_fields": ["source_payload_checksum", "export_checksum"],
        "required_jsonb_fields": ["payload", "lineage_refs", "evidence_refs"],
        "forbidden_live_behaviors": [
            "execute_live_database_writes",
            "create_supabase_client",
            "read_environment_variables",
            "network_calls",
            "llm_calls",
        ],
    }
    payload = dict(contract)
    contract["contract_checksum"] = _canonical_checksum(payload)
    return contract


def certify_d2_dashboard_supabase_schema(contract: Dict[str, Any] | None = None) -> Dict[str, Any]:
    contract = build_d2_dashboard_supabase_schema_contract() if contract is None else contract
    findings: List[str] = []
    tables = contract.get("table_inventory", [])
    migration_sql = Path(contract.get("migration_path", MIGRATION_PATH)).read_text(encoding="utf-8") if Path(contract.get("migration_path", MIGRATION_PATH)).exists() else ""
    missing_tables = [t for t in _REQUIRED_TABLES if t not in tables]
    if missing_tables:
        findings.append(f"missing_tables:{','.join(missing_tables)}")
    for table, cols in build_d2_dashboard_column_contract().items():
        got = set(contract.get("column_contract", {}).get(table, []))
        miss = [c for c in cols if c not in got]
        if miss:
            findings.append(f"missing_columns:{table}:{','.join(miss)}")
    for table in _REQUIRED_TABLES:
        if table not in migration_sql:
            findings.append(f"migration_missing_table:{table}")
    forbidden = [w for w in ["supabase.create_client", "os.environ", "requests.", "openai", "http://", "https://"] if w in migration_sql.lower()]
    if forbidden:
        findings.append("forbidden_capability_language_detected")
    status = CERTIFIED_DASHBOARD_SCHEMA_READY
    if findings:
        status = BLOCKED_DASHBOARD_SCHEMA_INVALID if any(f.startswith("missing_tables") for f in findings) else DEGRADED_DASHBOARD_SCHEMA_READY
    return {"status": status, "findings": findings, "contract_checksum": contract.get("contract_checksum", "")}


def build_d2_dashboard_supabase_schema_report() -> Dict[str, Any]:
    contract = build_d2_dashboard_supabase_schema_contract()
    certification = certify_d2_dashboard_supabase_schema(contract)
    return {
        "objective": "Implement deterministic Supabase schema contract for O6/O7/O8 dashboard operationalization outputs.",
        "contract": contract,
        "certification": certification,
    }
