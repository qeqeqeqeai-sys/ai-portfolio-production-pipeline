from __future__ import annotations

from typing import Any

from transmission_layers.asset_discovery.tier3h5.governance_history.persistence import LOG_DIR
from transmission_layers.asset_discovery.tier3h5.governance_query.serialization import write_stable_json

SUMMARY_PATHS = {
    "export": LOG_DIR / "tier3h5_bi_export_validation_summary.json",
    "semantic": LOG_DIR / "tier3h5_bi_semantic_validation_summary.json",
    "measure": LOG_DIR / "tier3h5_bi_measure_validation_summary.json",
    "relationship": LOG_DIR / "tier3h5_bi_relationship_validation_summary.json",
    "determinism": LOG_DIR / "tier3h5_bi_determinism_validation_summary.json",
    "phase4f": LOG_DIR / "tier3h5_phase4f_operational_validation_summary.json",
}


def build_phase4f_operational_validation_summary(validation: dict[str, Any]) -> dict[str, Any]:
    summary = {
        "validation_status": validation["validation_status"],
        "exported_tables_validated": validation["export"]["exported_tables_validated"],
        "semantic_tables_validated": validation["semantic"]["semantic_tables_validated"],
        "relationships_validated": validation["relationship"]["relationships_validated"],
        "measures_validated": validation["measure"]["measures_validated"],
        "deterministic_ordering_verified": validation["determinism"]["deterministic_ordering_verified"],
        "replay_equivalence_verified": validation["determinism"]["replay_equivalence_verified"],
        "orphan_reference_count": validation["relationship"]["orphan_reference_count"],
        "invalid_measure_reference_count": validation["measure"]["invalid_measure_reference_count"],
        "unstable_identifier_count": validation["relationship"]["unstable_identifier_count"],
        "governance_history_depth": validation["governance_history_depth"],
        "replay_mode": "advisory_only",
        "enforcement_enabled": False,
        "exact_match_only_preserved": True,
        "tier3h4_freeze_boundary_preserved": True,
    }
    write_stable_json(SUMMARY_PATHS["export"], validation["export"])
    write_stable_json(SUMMARY_PATHS["semantic"], validation["semantic"])
    write_stable_json(SUMMARY_PATHS["measure"], validation["measure"])
    write_stable_json(SUMMARY_PATHS["relationship"], validation["relationship"])
    write_stable_json(SUMMARY_PATHS["determinism"], validation["determinism"])
    write_stable_json(SUMMARY_PATHS["phase4f"], summary)
    return summary
