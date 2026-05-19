from __future__ import annotations

from typing import Any

VALID_AGGREGATIONS = {"sum", "count", "count_distinct", "count_rows", "max", "min", "avg"}


def validate_measure_catalog_metadata(measure_catalog: dict[str, Any], exports: dict[str, dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    measures = measure_catalog.get("measures", []) if isinstance(measure_catalog.get("measures"), list) else []
    exported_fields = {table: set(payload.get("fields", [])) for table, payload in exports.items() if isinstance(payload, dict)}
    names = [m.get("measure_name") for m in measures if isinstance(m, dict)]
    if len(names) != len(set(names)):
        errors.append("duplicate measure names detected")
    for measure in measures:
        if not isinstance(measure, dict):
            continue
        table, col = measure.get("table_name"), measure.get("column_name")
        if table not in exported_fields:
            errors.append(f"measure {measure.get('measure_name')} missing table {table}")
        elif col not in exported_fields[table]:
            errors.append(f"measure {measure.get('measure_name')} invalid column {table}.{col}")
        if measure.get("aggregation") not in VALID_AGGREGATIONS:
            errors.append(f"measure {measure.get('measure_name')} invalid aggregation")
    return {"measures_validated": len(measures), "invalid_measure_reference_count": len([e for e in errors if 'measure' in e]), "errors": sorted(errors)}
