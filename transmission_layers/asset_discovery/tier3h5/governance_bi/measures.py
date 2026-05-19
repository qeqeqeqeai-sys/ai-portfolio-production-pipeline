from __future__ import annotations

from typing import Any

from transmission_layers.asset_discovery.tier3h5.governance_history.hashing import stable_hash
from transmission_layers.asset_discovery.tier3h5.governance_query.serialization import advisory_contract

from .contracts import CONTRACT_VERSION, PHASE

MEASURE_DEFINITIONS: tuple[dict[str, str], ...] = (
    {"measure_name": "Total Governance Incidents", "table_name": "governance_incident_fact", "column_name": "incident_fact_id", "aggregation": "count_distinct", "filter": "none"},
    {"measure_name": "Persistent Governance Incidents", "table_name": "governance_continuity_fact", "column_name": "persistent_incident_count", "aggregation": "sum", "filter": "none"},
    {"measure_name": "Recurring Governance Incidents", "table_name": "governance_continuity_fact", "column_name": "recurring_incident_count", "aggregation": "sum", "filter": "none"},
    {"measure_name": "Transient Governance Incidents", "table_name": "governance_continuity_fact", "column_name": "transient_incident_count", "aggregation": "sum", "filter": "none"},
    {"measure_name": "Unresolved Governance Incidents", "table_name": "governance_incident_fact", "column_name": "is_unresolved", "aggregation": "sum", "filter": "none"},
    {"measure_name": "Escalated Governance Incidents", "table_name": "governance_escalation_fact", "column_name": "governance_review_recommended", "aggregation": "sum", "filter": "none"},
    {"measure_name": "Governance Trend Degrading Count", "table_name": "governance_trend_fact", "column_name": "governance_trend_status", "aggregation": "count_rows", "filter": "governance_trend_status == 'degrading'"},
    {"measure_name": "Governance Trend Improving Count", "table_name": "governance_trend_fact", "column_name": "governance_trend_status", "aggregation": "count_rows", "filter": "governance_trend_status == 'improving'"},
    {"measure_name": "Replay Instability Count", "table_name": "governance_incident_fact", "column_name": "governance_domain", "aggregation": "count_rows", "filter": "governance_domain == 'replay_governance_incident'"},
    {"measure_name": "Lineage Instability Count", "table_name": "governance_incident_fact", "column_name": "governance_domain", "aggregation": "count_rows", "filter": "governance_domain == 'lineage_integrity_incident'"},
    {"measure_name": "Provenance Degradation Count", "table_name": "governance_incident_fact", "column_name": "governance_domain", "aggregation": "count_rows", "filter": "governance_domain == 'provenance_governance_incident'"},
    {"measure_name": "Normalization Drift Count", "table_name": "governance_incident_fact", "column_name": "governance_domain", "aggregation": "count_rows", "filter": "governance_domain == 'normalization_governance_incident'"},
    {"measure_name": "Watchlist Persistence Count", "table_name": "governance_watchlist_fact", "column_name": "watchlist_count", "aggregation": "sum", "filter": "none"},
    {"measure_name": "Governance History Depth", "table_name": "governance_summary_snapshot", "column_name": "governance_history_depth", "aggregation": "max", "filter": "none"},
)


def build_measure_catalog() -> dict[str, Any]:
    measures = []
    for definition in MEASURE_DEFINITIONS:
        row = {
            **definition,
            "measure_id": f"tier3h5-bi-measure-{stable_hash(definition['measure_name'])[:12]}",
            "runtime_scoring": False,
            "metadata_only": True,
            "dashboard_label": definition["measure_name"],
            "dashboard_description": f"BI metadata definition for {definition['measure_name']}; calculated by the BI layer, not by governance runtime.",
        }
        measures.append(row)
    payload = {
        "phase": PHASE,
        "export_contract_version": CONTRACT_VERSION,
        "measure_catalog_status": "measure_catalog_available",
        "measure_count": len(measures),
        "measures": sorted(measures, key=lambda item: item["measure_name"]),
        "runtime_scoring_enabled": False,
        "metadata_only": True,
        **advisory_contract(),
    }
    payload["measure_catalog_hash"] = stable_hash(payload)
    return payload
