from __future__ import annotations

from typing import Any


def validate_semantic_readiness(semantic_layer: dict[str, Any]) -> dict[str, Any]:
    tables = semantic_layer.get("tables", []) if isinstance(semantic_layer, dict) else []
    relationships = semantic_layer.get("relationships", []) if isinstance(semantic_layer, dict) else []
    return {
        "semantic_layer_ready": bool(tables),
        "semantic_table_inventory_complete": bool(tables),
        "relationship_metadata_present": bool(relationships),
        "export_contract_present": bool(semantic_layer.get("export_contract_version")),
        "bi_field_naming_stable": all(" " not in field for table in tables for field in table.get("fields", [])),
        "semantic_tables_validated": len(tables),
    }
