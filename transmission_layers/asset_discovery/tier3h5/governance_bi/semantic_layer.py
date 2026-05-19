from __future__ import annotations

from typing import Any

from transmission_layers.asset_discovery.tier3h5.governance_history.hashing import stable_hash
from transmission_layers.asset_discovery.tier3h5.governance_query.serialization import advisory_contract

from .contracts import CONTRACT_VERSION, FACT_TABLES, PHASE


def build_semantic_layer() -> dict[str, Any]:
    tables = []
    for contract in FACT_TABLES:
        tables.append(
            {
                "table_name": contract.table_name,
                "primary_key": contract.primary_key,
                "artifact_path": str(contract.artifact_path),
                "fields": list(contract.fields),
                "date_fields": list(contract.date_fields),
                "categorical_fields": list(contract.categorical_fields),
                "numeric_measures": list(contract.numeric_fields),
                "default_aggregations": {field: "sum" for field in contract.numeric_fields},
                "dashboard_label": contract.table_name.replace("_", " ").title(),
                "dashboard_description": f"Power BI-ready advisory-only {contract.table_name.replace('_', ' ')} export for Tier 3H.5 governance dashboards.",
            }
        )
    relationships = [
        {
            "from_table": "governance_incident_fact",
            "from_column": "governance_domain",
            "to_table": "governance_domain_dimension",
            "to_column": "member_key",
            "cardinality": "many_to_one",
            "filter_direction": "dimension_to_fact",
        },
        {
            "from_table": "governance_incident_fact",
            "from_column": "severity",
            "to_table": "governance_severity_dimension",
            "to_column": "member_key",
            "cardinality": "many_to_one",
            "filter_direction": "dimension_to_fact",
        },
        {
            "from_table": "governance_incident_fact",
            "from_column": "governance_status",
            "to_table": "governance_status_dimension",
            "to_column": "member_key",
            "cardinality": "many_to_one",
            "filter_direction": "dimension_to_fact",
        },
        {
            "from_table": "governance_trend_fact",
            "from_column": "governance_trend_status",
            "to_table": "governance_trend_dimension",
            "to_column": "member_key",
            "cardinality": "many_to_one",
            "filter_direction": "dimension_to_fact",
        },
    ]
    payload = {
        "phase": PHASE,
        "export_contract_version": CONTRACT_VERSION,
        "semantic_layer_status": "semantic_layer_available",
        "semantic_layer_kind": "power_bi_governance_dashboard",
        "tables": tables,
        "relationships": relationships,
        "dashboard_posture": "read_only_advisory_only",
        "exact_match_only_preserved": True,
        "tier3h4_freeze_boundary_preserved": True,
        **advisory_contract(),
    }
    payload["semantic_layer_hash"] = stable_hash(payload)
    return payload
