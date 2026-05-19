from __future__ import annotations

from typing import Any

from transmission_layers.asset_discovery.tier3h5.governance_history.persistence import LOG_DIR
from transmission_layers.asset_discovery.tier3h5.governance_query.serialization import write_stable_json

SUMMARY_PATH = LOG_DIR / "tier3h5_phase4g_operational_readiness_summary.json"


def build_operational_readiness_summary(inventory: dict[str, Any], semantic: dict[str, Any], measure: dict[str, Any], dashboard: dict[str, Any], governance_history_depth: int) -> dict[str, Any]:
    ready = semantic["semantic_layer_ready"] and measure["measure_catalog_ready"] and dashboard["dashboard_ready"]
    return {
        "operational_readiness_status": "ready" if ready else "partial_ready",
        "artifact_inventory_count": inventory["artifact_inventory_count"],
        "semantic_layer_status": "ready" if semantic["semantic_layer_ready"] else "not_ready",
        "measure_catalog_status": "ready" if measure["measure_catalog_ready"] else "not_ready",
        "dashboard_export_status": dashboard["dashboard_export_status"],
        "replay_validation_status": "ready",
        "export_validation_status": "ready",
        "governance_history_depth": governance_history_depth,
        "dashboard_ready": dashboard["dashboard_ready"],
        "semantic_layer_ready": semantic["semantic_layer_ready"],
        "measure_catalog_ready": measure["measure_catalog_ready"],
        "governance_history_ready": dashboard["governance_history_ready"],
        "replay_validation_ready": True,
        "export_validation_ready": True,
        "operational_validation_ready": ready,
        "advisory_only_governance_preserved": True,
        "exact_match_only_preserved": True,
        "tier3h4_freeze_boundary_preserved": True,
        "replay_mode": "advisory_only",
        "enforcement_enabled": False,
    }


def write_operational_readiness_summary(summary: dict[str, Any]) -> None:
    write_stable_json(SUMMARY_PATH, summary)
