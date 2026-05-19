from __future__ import annotations

from typing import Any

from .contracts import DIMENSION_MEMBERS, FACT_TABLES


def validate_export_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    table_name = payload.get("table_name")
    contract = next((item for item in FACT_TABLES if item.table_name == table_name), None)
    if contract is None:
        return [f"unknown table: {table_name}"]
    if payload.get("replay_mode") != "advisory_only":
        errors.append(f"{table_name}: replay_mode must be advisory_only")
    if payload.get("enforcement_enabled") is not False:
        errors.append(f"{table_name}: enforcement_enabled must be false")
    if payload.get("primary_key") != contract.primary_key:
        errors.append(f"{table_name}: primary key changed")
    if payload.get("fields") != list(contract.fields):
        errors.append(f"{table_name}: field order changed")
    rows = payload.get("rows", []) if isinstance(payload.get("rows"), list) else []
    pks = [row.get(contract.primary_key) for row in rows if isinstance(row, dict)]
    if pks != sorted(pks):
        errors.append(f"{table_name}: row ordering is not deterministic by primary key")
    if len(pks) != len(set(pks)):
        errors.append(f"{table_name}: primary keys are not unique")
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"{table_name}: row {index} is not an object")
            continue
        missing = [field for field in contract.fields if field not in row]
        if missing:
            errors.append(f"{table_name}: row {index} missing fields {missing}")
        if row.get("replay_mode") != "advisory_only":
            errors.append(f"{table_name}: row {index} replay_mode must be advisory_only")
        if row.get("enforcement_enabled") is not False:
            errors.append(f"{table_name}: row {index} enforcement_enabled must be false")
    return errors


def validate_dimensions(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    dimensions = payload.get("dimensions", {}) if isinstance(payload.get("dimensions"), dict) else {}
    for name, members in DIMENSION_MEMBERS.items():
        rows = dimensions.get(name, []) if isinstance(dimensions.get(name), list) else []
        actual = {row.get("member_key") for row in rows if isinstance(row, dict)}
        expected = set(members)
        if actual != expected:
            errors.append(f"{name}: expected members {sorted(expected)}, found {sorted(actual)}")
        for index, row in enumerate(rows):
            if row.get("replay_mode") != "advisory_only" or row.get("enforcement_enabled") is not False:
                errors.append(f"{name}: row {index} must remain advisory-only and non-enforcing")
    return errors


def validate_semantic_layer(semantic_layer: dict[str, Any], exports: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    exported_fields = {name: set(payload.get("fields", [])) for name, payload in exports.items() if isinstance(payload, dict)}
    for table in semantic_layer.get("tables", []):
        if not isinstance(table, dict):
            continue
        name = table.get("table_name")
        fields = set(table.get("fields", []))
        if name not in exported_fields:
            errors.append(f"semantic layer references missing table {name}")
        elif not fields <= exported_fields[name]:
            errors.append(f"semantic layer {name} references invalid fields {sorted(fields - exported_fields[name])}")
    for relationship in semantic_layer.get("relationships", []):
        if not isinstance(relationship, dict):
            continue
        from_table = relationship.get("from_table")
        from_column = relationship.get("from_column")
        if from_table in exported_fields and from_column not in exported_fields[from_table]:
            errors.append(f"relationship references invalid field {from_table}.{from_column}")
    if semantic_layer.get("replay_mode") != "advisory_only" or semantic_layer.get("enforcement_enabled") is not False:
        errors.append("semantic layer must remain advisory-only and non-enforcing")
    return errors


def validate_measure_catalog(measure_catalog: dict[str, Any], exports: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    exported_fields = {name: set(payload.get("fields", [])) for name, payload in exports.items() if isinstance(payload, dict)}
    for measure in measure_catalog.get("measures", []):
        if not isinstance(measure, dict):
            continue
        table = measure.get("table_name")
        column = measure.get("column_name")
        if table not in exported_fields:
            errors.append(f"measure {measure.get('measure_name')} references missing table {table}")
        elif column not in exported_fields[table]:
            errors.append(f"measure {measure.get('measure_name')} references invalid column {table}.{column}")
        if measure.get("runtime_scoring") is not False or measure.get("metadata_only") is not True:
            errors.append(f"measure {measure.get('measure_name')} must be metadata-only with runtime scoring disabled")
    if measure_catalog.get("replay_mode") != "advisory_only" or measure_catalog.get("enforcement_enabled") is not False:
        errors.append("measure catalog must remain advisory-only and non-enforcing")
    return errors


def validate_bi_exports(exports: dict[str, dict[str, Any]], dimensions: dict[str, Any], semantic_layer: dict[str, Any], measure_catalog: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    for contract in FACT_TABLES:
        payload = exports.get(contract.table_name)
        if not payload:
            errors.append(f"missing export table {contract.table_name}")
        else:
            errors.extend(validate_export_payload(payload))
    errors.extend(validate_dimensions(dimensions))
    errors.extend(validate_semantic_layer(semantic_layer, exports))
    errors.extend(validate_measure_catalog(measure_catalog, exports))
    return {"validation_status": "valid" if not errors else "invalid", "validation_error_count": len(errors), "validation_errors": sorted(errors)}
