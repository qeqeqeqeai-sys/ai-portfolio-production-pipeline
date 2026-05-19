from __future__ import annotations

from typing import Any

from transmission_layers.asset_discovery.tier3h5.governance_history.hashing import stable_hash
from transmission_layers.asset_discovery.tier3h5.governance_query.serialization import advisory_contract, write_stable_json

from .contracts import (
    CONTINUITY_FACT,
    DIMENSIONS_PATH,
    ESCALATION_FACT,
    FACT_TABLES,
    INCIDENT_FACT,
    MEASURE_CATALOG_PATH,
    PHASE,
    PHASE4E_SUMMARY_PATH,
    SEMANTIC_LAYER_PATH,
    SUMMARY_SNAPSHOT,
    TREND_FACT,
    WATCHLIST_FACT,
)
from .exports import bi_history_status, build_all_export_tables
from .measures import build_measure_catalog
from .semantic_layer import build_semantic_layer
from .validation import validate_bi_exports


def _write_fact_exports(exports: dict[str, dict[str, Any]]) -> None:
    for contract in FACT_TABLES:
        write_stable_json(contract.artifact_path, exports[contract.table_name])


def _summary(exports: dict[str, dict[str, Any]], dimensions: dict[str, Any], semantic_layer: dict[str, Any], measure_catalog: dict[str, Any], validation: dict[str, Any]) -> dict[str, Any]:
    incident_depth = int(exports[INCIDENT_FACT.table_name].get("governance_history_depth", 0) or 0)
    rows_by_table = {contract.table_name: int(exports[contract.table_name].get("row_count", 0) or 0) for contract in FACT_TABLES}
    summary = {
        "phase": PHASE,
        "bi_export_status": "bi_exports_available" if validation["validation_status"] == "valid" else "bi_exports_invalid",
        "bi_history_status": bi_history_status(incident_depth),
        "exported_table_count": len(FACT_TABLES),
        "exported_dimension_count": int(dimensions.get("dimension_count", 0) or 0),
        "exported_measure_count": int(measure_catalog.get("measure_count", 0) or 0),
        "semantic_layer_status": semantic_layer.get("semantic_layer_status", "semantic_layer_unavailable"),
        "dashboard_ready": validation["validation_status"] == "valid",
        "governance_history_depth": incident_depth,
        "rows_by_table": rows_by_table,
        "validation_status": validation["validation_status"],
        "validation_error_count": validation["validation_error_count"],
        "exact_match_only_preserved": True,
        "tier3h4_freeze_boundary_preserved": True,
        "read_only_export_behavior_preserved": True,
        "fuzzy_matching_enabled": False,
        "semantic_matching_enabled": False,
        "canonical_override_enabled": False,
        "scoring_mutation_enabled": False,
        "propagation_mutation_enabled": False,
        "confidence_mutation_enabled": False,
        "reconciliation_mutation_enabled": False,
        **advisory_contract(),
    }
    summary["phase4e_summary_hash"] = stable_hash(summary)
    return summary


def build_bi_export_artifacts() -> dict[str, Any]:
    all_exports = build_all_export_tables()
    fact_exports = {contract.table_name: all_exports[contract.table_name] for contract in FACT_TABLES}
    dimensions = all_exports["governance_dimensions"]
    semantic_layer = build_semantic_layer()
    measure_catalog = build_measure_catalog()
    validation = validate_bi_exports(fact_exports, dimensions, semantic_layer, measure_catalog)
    summary = _summary(fact_exports, dimensions, semantic_layer, measure_catalog, validation)
    return {
        **fact_exports,
        "governance_dimensions": dimensions,
        "semantic_layer": semantic_layer,
        "measure_catalog": measure_catalog,
        "validation": validation,
        "summary": summary,
    }


def write_bi_export_artifacts() -> dict[str, Any]:
    artifacts = build_bi_export_artifacts()
    fact_exports = {contract.table_name: artifacts[contract.table_name] for contract in FACT_TABLES}
    _write_fact_exports(fact_exports)
    write_stable_json(DIMENSIONS_PATH, artifacts["governance_dimensions"])
    write_stable_json(SEMANTIC_LAYER_PATH, artifacts["semantic_layer"])
    write_stable_json(MEASURE_CATALOG_PATH, artifacts["measure_catalog"])
    write_stable_json(PHASE4E_SUMMARY_PATH, artifacts["summary"])
    return artifacts


if __name__ == "__main__":
    write_bi_export_artifacts()
