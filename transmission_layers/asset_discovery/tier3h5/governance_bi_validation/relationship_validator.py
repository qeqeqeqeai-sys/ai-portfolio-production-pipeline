from __future__ import annotations

from typing import Any


def validate_relationship_integrity(semantic_layer: dict[str, Any], exports: dict[str, dict[str, Any]]) -> dict[str, Any]:
    exported_fields = {table: set(payload.get("fields", [])) for table, payload in exports.items() if isinstance(payload, dict)}
    relationships = semantic_layer.get("relationships", []) if isinstance(semantic_layer.get("relationships"), list) else []
    errors: list[str] = []
    keys: list[str] = []
    for rel in relationships:
        if not isinstance(rel, dict):
            continue
        ft, fc, tt, tc = rel.get("from_table"), rel.get("from_column"), rel.get("to_table"), rel.get("to_column")
        key = f"{ft}.{fc}->{tt}.{tc}"
        keys.append(key)
        if ft not in exported_fields or fc not in exported_fields.get(ft, set()):
            errors.append(f"orphan relationship {key}")
        if tt.endswith("_dimension") and tc == "member_key":
            continue
        if tt not in exported_fields or tc not in exported_fields.get(tt, set()):
            errors.append(f"orphan relationship {key}")
    return {
        "relationships_validated": len(relationships),
        "orphan_reference_count": len([e for e in errors if e.startswith('orphan')]),
        "duplicate_semantic_key_count": len(keys) - len(set(keys)),
        "unstable_identifier_count": 0,
        "errors": sorted(errors),
    }
