from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from transmission_layers.asset_discovery.tier3h5.governance_history.persistence import LOG_DIR

CONTRACT_VERSION = "tier3h5_phase4e_bi_contract_v1"
PHASE = "tier3h5_phase4e"

INCIDENT_FACT_PATH = LOG_DIR / "tier3h5_bi_governance_incident_fact.json"
ESCALATION_FACT_PATH = LOG_DIR / "tier3h5_bi_governance_escalation_fact.json"
WATCHLIST_FACT_PATH = LOG_DIR / "tier3h5_bi_governance_watchlist_fact.json"
TREND_FACT_PATH = LOG_DIR / "tier3h5_bi_governance_trend_fact.json"
CONTINUITY_FACT_PATH = LOG_DIR / "tier3h5_bi_governance_continuity_fact.json"
SUMMARY_SNAPSHOT_PATH = LOG_DIR / "tier3h5_bi_governance_summary_snapshot.json"
DIMENSIONS_PATH = LOG_DIR / "tier3h5_bi_governance_dimensions.json"
SEMANTIC_LAYER_PATH = LOG_DIR / "tier3h5_bi_semantic_layer.json"
MEASURE_CATALOG_PATH = LOG_DIR / "tier3h5_bi_measure_catalog.json"
PHASE4E_SUMMARY_PATH = LOG_DIR / "tier3h5_phase4e_bi_export_summary.json"


@dataclass(frozen=True)
class TableContract:
    table_name: str
    artifact_path: Path
    primary_key: str
    fields: tuple[str, ...]
    date_fields: tuple[str, ...] = ()
    categorical_fields: tuple[str, ...] = ()
    numeric_fields: tuple[str, ...] = ()


INCIDENT_FACT = TableContract(
    "governance_incident_fact",
    INCIDENT_FACT_PATH,
    "incident_fact_id",
    (
        "incident_fact_id",
        "incident_history_id",
        "incident_id",
        "incident_key",
        "governance_domain",
        "governance_status",
        "severity",
        "signal",
        "entity",
        "registry_source",
        "run_date_sgt",
        "is_unresolved",
        "incident_hash",
        "incident_lifecycle_hash",
        "replay_mode",
        "enforcement_enabled",
    ),
    date_fields=("run_date_sgt",),
    categorical_fields=("governance_domain", "governance_status", "severity", "signal", "entity", "registry_source"),
    numeric_fields=("is_unresolved",),
)

ESCALATION_FACT = TableContract(
    "governance_escalation_fact",
    ESCALATION_FACT_PATH,
    "escalation_fact_id",
    (
        "escalation_fact_id",
        "escalation_history_id",
        "escalation_status",
        "governance_review_recommended",
        "run_date_sgt",
        "escalation_input_count",
        "escalation_summary_hash",
        "escalation_history_hash",
        "replay_mode",
        "enforcement_enabled",
    ),
    date_fields=("run_date_sgt",),
    categorical_fields=("escalation_status",),
    numeric_fields=("governance_review_recommended", "escalation_input_count"),
)

WATCHLIST_FACT = TableContract(
    "governance_watchlist_fact",
    WATCHLIST_FACT_PATH,
    "watchlist_fact_id",
    (
        "watchlist_fact_id",
        "watchlist_history_id",
        "watchlist_name",
        "watchlist_count",
        "watchlist_item_hash_count",
        "run_date_sgt",
        "watchlist_evolution_hash",
        "replay_mode",
        "enforcement_enabled",
    ),
    date_fields=("run_date_sgt",),
    categorical_fields=("watchlist_name",),
    numeric_fields=("watchlist_count", "watchlist_item_hash_count"),
)

TREND_FACT = TableContract(
    "governance_trend_fact",
    TREND_FACT_PATH,
    "trend_fact_id",
    (
        "trend_fact_id",
        "governance_trend_status",
        "escalation_trend_status",
        "replay_stability_trend",
        "lineage_stability_trend",
        "normalization_drift_trend",
        "provenance_quality_trend",
        "cross_registry_stability_trend",
        "unresolved_growth_trend",
        "duplicate_lineage_trend",
        "trend_window",
        "run_date_sgt",
        "governance_trend_hash",
        "replay_mode",
        "enforcement_enabled",
    ),
    date_fields=("run_date_sgt",),
    categorical_fields=(
        "governance_trend_status",
        "escalation_trend_status",
        "replay_stability_trend",
        "lineage_stability_trend",
        "normalization_drift_trend",
        "provenance_quality_trend",
        "cross_registry_stability_trend",
        "unresolved_growth_trend",
        "duplicate_lineage_trend",
    ),
    numeric_fields=("trend_window",),
)

CONTINUITY_FACT = TableContract(
    "governance_continuity_fact",
    CONTINUITY_FACT_PATH,
    "continuity_fact_id",
    (
        "continuity_fact_id",
        "historical_continuity_status",
        "governance_history_depth",
        "persistent_incident_count",
        "recurring_incident_count",
        "transient_incident_count",
        "run_date_sgt",
        "continuity_hash",
        "replay_mode",
        "enforcement_enabled",
    ),
    date_fields=("run_date_sgt",),
    categorical_fields=("historical_continuity_status",),
    numeric_fields=("governance_history_depth", "persistent_incident_count", "recurring_incident_count", "transient_incident_count"),
)

SUMMARY_SNAPSHOT = TableContract(
    "governance_summary_snapshot",
    SUMMARY_SNAPSHOT_PATH,
    "summary_snapshot_id",
    (
        "summary_snapshot_id",
        "snapshot_kind",
        "dashboard_generated_at",
        "bi_history_status",
        "governance_history_depth",
        "unresolved_governance_totals",
        "replay_instability_totals",
        "lineage_instability_totals",
        "normalization_drift_totals",
        "provenance_degradation_totals",
        "cross_registry_instability_totals",
        "run_date_sgt",
        "dashboard_view_hash",
        "replay_mode",
        "enforcement_enabled",
    ),
    date_fields=("dashboard_generated_at", "run_date_sgt"),
    categorical_fields=("snapshot_kind", "bi_history_status"),
    numeric_fields=(
        "governance_history_depth",
        "unresolved_governance_totals",
        "replay_instability_totals",
        "lineage_instability_totals",
        "normalization_drift_totals",
        "provenance_degradation_totals",
        "cross_registry_instability_totals",
    ),
)

FACT_TABLES = (INCIDENT_FACT, ESCALATION_FACT, WATCHLIST_FACT, TREND_FACT, CONTINUITY_FACT, SUMMARY_SNAPSHOT)

DIMENSION_MEMBERS = {
    "governance_domain_dimension": [
        "cross_registry_governance_incident",
        "lineage_integrity_incident",
        "normalization_governance_incident",
        "provenance_governance_incident",
        "replay_governance_incident",
        "unknown",
    ],
    "governance_status_dimension": [
        "advisory_attention",
        "bi_history_initializing",
        "critical_governance_instability",
        "governance_review_recommended",
        "governance_risk",
        "informational",
        "insufficient_bi_history",
        "partial_bi_history_available",
        "stable_bi_history_available",
        "unknown",
    ],
    "governance_trend_dimension": ["degrading", "improving", "insufficient_history", "stable", "unknown", "unstable"],
    "governance_severity_dimension": [
        "advisory_attention",
        "critical_governance_instability",
        "elevated_attention",
        "governance_review_recommended",
        "governance_risk",
        "informational",
        "unknown",
    ],
}
