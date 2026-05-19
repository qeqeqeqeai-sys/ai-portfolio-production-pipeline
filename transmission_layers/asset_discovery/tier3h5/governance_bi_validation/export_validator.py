from __future__ import annotations

from typing import Any

from transmission_layers.asset_discovery.tier3h5.governance_bi.contracts import FACT_TABLES


def validate_fact_exports(exports: dict[str, dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    validated = 0
    for contract in FACT_TABLES:
        payload = exports.get(contract.table_name)
        if not isinstance(payload, dict):
            errors.append(f"missing export table {contract.table_name}")
            continue
        validated += 1
        if payload.get("fields") != list(contract.fields):
            errors.append(f"{contract.table_name}: field ordering mismatch")
        if payload.get("primary_key") != contract.primary_key:
            errors.append(f"{contract.table_name}: primary key mismatch")
        if payload.get("append_history_compatible") is not True:
            errors.append(f"{contract.table_name}: append-history compatibility must be true")
        rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
        keys = [row.get(contract.primary_key) for row in rows if isinstance(row, dict)]
        if keys != sorted(keys):
            errors.append(f"{contract.table_name}: unstable primary key ordering")
        if len(keys) != len(set(keys)):
            errors.append(f"{contract.table_name}: duplicate primary keys")
    return {"exported_tables_validated": validated, "errors": sorted(errors)}
