from __future__ import annotations

from typing import Any


def validate_semantic_layer_metadata(semantic_layer: dict[str, Any], exports: dict[str, dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    exported_fields = {table: set(payload.get("fields", [])) for table, payload in exports.items() if isinstance(payload, dict)}
    tables = semantic_layer.get("tables", []) if isinstance(semantic_layer.get("tables"), list) else []
    relationships = semantic_layer.get("relationships", []) if isinstance(semantic_layer.get("relationships"), list) else []
    validated = 0
    for table in tables:
        if not isinstance(table, dict):
            continue
        validated += 1
        name = table.get("table_name")
        if name not in exported_fields:
            errors.append(f"semantic table missing export: {name}")
            continue
        fields = set(table.get("fields", []))
        missing = fields - exported_fields[name]
        if missing:
            errors.append(f"semantic table {name} invalid fields {sorted(missing)}")
        if not table.get("dashboard_label") or not table.get("dashboard_description"):
            errors.append(f"semantic table {name} missing dashboard metadata")
    for rel in relationships:
        if not isinstance(rel, dict):
            continue
        ft, fc, tt, tc = rel.get("from_table"), rel.get("from_column"), rel.get("to_table"), rel.get("to_column")
        if ft not in exported_fields or fc not in exported_fields.get(ft, set()):
            errors.append(f"invalid relationship source {ft}.{fc}")
        if not (tt.endswith("_dimension") and tc == "member_key"):
            if tt not in exported_fields or tc not in exported_fields.get(tt, set()):
                errors.append(f"invalid relationship target {tt}.{tc}")
    return {"semantic_tables_validated": validated, "relationships_validated": len(relationships), "errors": sorted(errors)}
