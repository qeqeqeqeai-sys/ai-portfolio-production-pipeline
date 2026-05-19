from __future__ import annotations

from typing import Any

from transmission_layers.asset_discovery.tier3h5.governance_bi.exports import bi_history_status

from .determinism_validator import validate_determinism
from .export_validator import validate_fact_exports
from .measure_validator import validate_measure_catalog_metadata
from .relationship_validator import validate_relationship_integrity
from .semantic_validator import validate_semantic_layer_metadata


def validate_operational_artifacts(current: dict[str, Any], replay: dict[str, Any]) -> dict[str, Any]:
    exports = {k: v for k, v in current.items() if k.endswith("_fact") or k == "governance_summary_snapshot"}
    export_out = validate_fact_exports(exports)
    semantic_out = validate_semantic_layer_metadata(current["semantic_layer"], exports)
    measure_out = validate_measure_catalog_metadata(current["measure_catalog"], exports)
    relationship_out = validate_relationship_integrity(current["semantic_layer"], exports)
    determinism_out = validate_determinism(current, replay)
    all_errors = sorted(export_out["errors"] + semantic_out["errors"] + measure_out["errors"] + relationship_out["errors"] + determinism_out["errors"])
    depth = int(current.get("summary", {}).get("governance_history_depth", 0) or 0)
    return {
        "validation_status": "valid" if not all_errors else "invalid",
        "governance_history_depth": depth,
        "bi_history_status": bi_history_status(depth),
        "export": export_out,
        "semantic": semantic_out,
        "measure": measure_out,
        "relationship": relationship_out,
        "determinism": determinism_out,
        "validation_errors": all_errors,
    }
