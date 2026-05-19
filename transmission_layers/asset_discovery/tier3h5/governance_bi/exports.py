from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from transmission_layers.asset_discovery.tier3h5.governance_history.artifacts import CONTINUITY_HISTORY_PATH, HISTORY_SUMMARY_PATH, TREND_HISTORY_PATH, TREND_SUMMARY_PATH
from transmission_layers.asset_discovery.tier3h5.governance_history.hashing import stable_hash
from transmission_layers.asset_discovery.tier3h5.governance_history.persistence import ESCALATION_HISTORY_PATH, INCIDENT_HISTORY_PATH, WATCHLIST_HISTORY_PATH, load_json
from transmission_layers.asset_discovery.tier3h5.governance_query.base import history_rows, stable_sort
from transmission_layers.asset_discovery.tier3h5.governance_query.dashboard_views import build_dashboard_views
from transmission_layers.asset_discovery.tier3h5.governance_query.serialization import advisory_contract, stable_row

from .contracts import (
    CONTRACT_VERSION,
    CONTINUITY_FACT,
    DIMENSION_MEMBERS,
    ESCALATION_FACT,
    FACT_TABLES,
    INCIDENT_FACT,
    PHASE,
    SUMMARY_SNAPSHOT,
    TREND_FACT,
    WATCHLIST_FACT,
    TableContract,
)

UNRESOLVED_SEVERITIES = {"governance_risk", "governance_review_recommended", "critical_governance_instability"}


def bi_history_status(depth: int) -> str:
    if depth <= 0:
        return "insufficient_bi_history"
    if depth == 1:
        return "bi_history_initializing"
    if depth < 3:
        return "partial_bi_history_available"
    return "stable_bi_history_available"


def _run_date(row: dict[str, Any]) -> str:
    return str(row.get("run_date_sgt") or row.get("run_date") or row.get("archived_at_sgt") or row.get("created_at") or "deterministic_replay")


def _pk(prefix: str, row: dict[str, Any]) -> str:
    return f"tier3h5-bi-{prefix}-{stable_hash(row)[:16]}"


def _bool_int(value: Any) -> int:
    return 1 if value is True else 0


def _table_payload(contract: TableContract, rows: Iterable[dict[str, Any]], depth: int) -> dict[str, Any]:
    ordered_rows = sorted((stable_row(row, contract.fields) for row in rows), key=lambda row: str(row.get(contract.primary_key, stable_hash(row))))
    payload = {
        "phase": PHASE,
        "export_contract_version": CONTRACT_VERSION,
        "table_name": contract.table_name,
        "primary_key": contract.primary_key,
        "fields": list(contract.fields),
        "date_fields": list(contract.date_fields),
        "categorical_fields": list(contract.categorical_fields),
        "numeric_fields": list(contract.numeric_fields),
        "append_history_compatible": True,
        "dashboard_ready": True,
        "bi_history_status": bi_history_status(depth),
        "governance_history_depth": depth,
        "row_count": len(ordered_rows),
        "rows": ordered_rows,
        **advisory_contract(),
    }
    payload["export_hash"] = stable_hash(payload)
    return payload


def build_incident_fact() -> dict[str, Any]:
    source_rows = history_rows(INCIDENT_HISTORY_PATH)
    rows: list[dict[str, Any]] = []
    for row in stable_sort(source_rows):
        severity = str(row.get("severity") or "unknown")
        out = {
            "incident_fact_id": _pk("incident", {"history_id": row.get("incident_history_id"), "key": row.get("incident_key"), "hash": row.get("incident_lifecycle_hash")}),
            "incident_history_id": row.get("incident_history_id", "unknown"),
            "incident_id": row.get("incident_id", "unknown"),
            "incident_key": row.get("incident_key", "unknown"),
            "governance_domain": row.get("category", "unknown"),
            "governance_status": severity,
            "severity": severity,
            "signal": row.get("signal", "unknown"),
            "entity": row.get("entity", "unknown"),
            "registry_source": row.get("registry_source", "unknown"),
            "run_date_sgt": _run_date(row),
            "is_unresolved": 1 if severity in UNRESOLVED_SEVERITIES else 0,
            "incident_hash": row.get("incident_hash", stable_hash(row)),
            "incident_lifecycle_hash": row.get("incident_lifecycle_hash", stable_hash(row)),
            "replay_mode": "advisory_only",
            "enforcement_enabled": False,
        }
        rows.append(out)
    return _table_payload(INCIDENT_FACT, rows, len(source_rows))


def build_escalation_fact() -> dict[str, Any]:
    source_rows = history_rows(ESCALATION_HISTORY_PATH)
    rows = []
    for row in stable_sort(source_rows):
        inputs = row.get("escalation_inputs", {}) if isinstance(row.get("escalation_inputs"), dict) else {}
        out = {
            "escalation_fact_id": _pk("escalation", {"history_id": row.get("escalation_history_id"), "hash": row.get("escalation_history_hash")}),
            "escalation_history_id": row.get("escalation_history_id", "unknown"),
            "escalation_status": row.get("escalation_status", "no_escalation"),
            "governance_review_recommended": _bool_int(row.get("governance_review_recommended")),
            "run_date_sgt": _run_date(row),
            "escalation_input_count": len(inputs),
            "escalation_summary_hash": row.get("escalation_summary_hash", "unknown"),
            "escalation_history_hash": row.get("escalation_history_hash", stable_hash(row)),
            "replay_mode": "advisory_only",
            "enforcement_enabled": False,
        }
        rows.append(out)
    return _table_payload(ESCALATION_FACT, rows, len(source_rows))


def build_watchlist_fact() -> dict[str, Any]:
    source_rows = history_rows(WATCHLIST_HISTORY_PATH)
    rows = []
    for row in stable_sort(source_rows):
        item_hashes = row.get("watchlist_item_hashes", []) if isinstance(row.get("watchlist_item_hashes"), list) else []
        out = {
            "watchlist_fact_id": _pk("watchlist", {"history_id": row.get("watchlist_history_id"), "hash": row.get("watchlist_evolution_hash")}),
            "watchlist_history_id": row.get("watchlist_history_id", "unknown"),
            "watchlist_name": row.get("watchlist_name", "unknown"),
            "watchlist_count": int(row.get("watchlist_count", 0) or 0),
            "watchlist_item_hash_count": len(item_hashes),
            "run_date_sgt": _run_date(row),
            "watchlist_evolution_hash": row.get("watchlist_evolution_hash", stable_hash(row)),
            "replay_mode": "advisory_only",
            "enforcement_enabled": False,
        }
        rows.append(out)
    return _table_payload(WATCHLIST_FACT, rows, len(source_rows))


def _trend_sources() -> list[dict[str, Any]]:
    rows = history_rows(TREND_HISTORY_PATH)
    if rows:
        return rows
    summary = load_json(TREND_SUMMARY_PATH)
    return [summary] if summary else []


def build_trend_fact() -> dict[str, Any]:
    source_rows = _trend_sources()
    rows = []
    for row in stable_sort(source_rows):
        out = {
            "trend_fact_id": _pk("trend", {"hash": row.get("governance_trend_hash"), "window": row.get("trend_window"), "date": _run_date(row)}),
            "governance_trend_status": row.get("governance_trend_status", "insufficient_history"),
            "escalation_trend_status": row.get("escalation_trend_status", "insufficient_history"),
            "replay_stability_trend": row.get("replay_stability_trend", "insufficient_history"),
            "lineage_stability_trend": row.get("lineage_stability_trend", "insufficient_history"),
            "normalization_drift_trend": row.get("normalization_drift_trend", "insufficient_history"),
            "provenance_quality_trend": row.get("provenance_quality_trend", "insufficient_history"),
            "cross_registry_stability_trend": row.get("cross_registry_stability_trend", "insufficient_history"),
            "unresolved_growth_trend": row.get("unresolved_growth_trend", "insufficient_history"),
            "duplicate_lineage_trend": row.get("duplicate_lineage_trend", "insufficient_history"),
            "trend_window": int(row.get("trend_window", 0) or 0),
            "run_date_sgt": _run_date(row),
            "governance_trend_hash": row.get("governance_trend_hash", stable_hash(row)),
            "replay_mode": "advisory_only",
            "enforcement_enabled": False,
        }
        rows.append(out)
    return _table_payload(TREND_FACT, rows, len(source_rows))


def _continuity_sources() -> list[dict[str, Any]]:
    rows = history_rows(CONTINUITY_HISTORY_PATH)
    if rows:
        return rows
    summary = load_json(HISTORY_SUMMARY_PATH)
    return [summary] if summary else []


def build_continuity_fact() -> dict[str, Any]:
    source_rows = _continuity_sources()
    rows = []
    for row in stable_sort(source_rows):
        out = {
            "continuity_fact_id": _pk("continuity", {"hash": row.get("continuity_hash"), "depth": row.get("governance_history_depth"), "date": _run_date(row)}),
            "historical_continuity_status": row.get("historical_continuity_status", "insufficient_governance_history"),
            "governance_history_depth": int(row.get("governance_history_depth", 0) or 0),
            "persistent_incident_count": int(row.get("persistent_incident_count", 0) or 0),
            "recurring_incident_count": int(row.get("recurring_incident_count", 0) or 0),
            "transient_incident_count": int(row.get("transient_incident_count", 0) or 0),
            "run_date_sgt": _run_date(row),
            "continuity_hash": row.get("continuity_hash", stable_hash(row)),
            "replay_mode": "advisory_only",
            "enforcement_enabled": False,
        }
        rows.append(out)
    return _table_payload(CONTINUITY_FACT, rows, len(source_rows))


def build_summary_snapshot() -> dict[str, Any]:
    views = build_dashboard_views()
    governance = views["governance_summary"]
    operational = views["operational_summary"]
    depth = int(governance.get("governance_history_depth", 0) or 0)
    row = {
        "summary_snapshot_id": _pk("summary", {"kind": "operational_summary", "hash": operational.get("dashboard_view_hash")}),
        "snapshot_kind": "operational_summary",
        "dashboard_generated_at": operational.get("dashboard_generated_at", "deterministic_replay"),
        "bi_history_status": bi_history_status(depth),
        "governance_history_depth": depth,
        "unresolved_governance_totals": int(operational.get("unresolved_governance_totals", 0) or 0),
        "replay_instability_totals": int(operational.get("replay_instability_totals", 0) or 0),
        "lineage_instability_totals": int(operational.get("lineage_instability_totals", 0) or 0),
        "normalization_drift_totals": int(operational.get("normalization_drift_totals", 0) or 0),
        "provenance_degradation_totals": int(operational.get("provenance_degradation_totals", 0) or 0),
        "cross_registry_instability_totals": int(operational.get("cross_registry_instability_totals", 0) or 0),
        "run_date_sgt": operational.get("dashboard_generated_at", "deterministic_replay"),
        "dashboard_view_hash": operational.get("dashboard_view_hash", stable_hash(operational)),
        "replay_mode": "advisory_only",
        "enforcement_enabled": False,
    }
    return _table_payload(SUMMARY_SNAPSHOT, [row], depth)


def build_dimension_exports() -> dict[str, Any]:
    dimensions: dict[str, list[dict[str, Any]]] = {}
    for dimension_name, members in sorted(DIMENSION_MEMBERS.items()):
        key_field = dimension_name.replace("governance_", "").replace("_dimension", "")
        rows = []
        for member in sorted(members):
            rows.append(
                {
                    "dimension_id": f"tier3h5-bi-{dimension_name}-{stable_hash(member)[:12]}",
                    "dimension_name": dimension_name,
                    "member_key": member,
                    "member_label": member.replace("_", " ").title(),
                    "replay_mode": "advisory_only",
                    "enforcement_enabled": False,
                    key_field: member,
                }
            )
        dimensions[dimension_name] = rows
    payload = {
        "phase": PHASE,
        "export_contract_version": CONTRACT_VERSION,
        "artifact_kind": "governance_bi_dimensions",
        "dimension_count": len(dimensions),
        "dimensions": dimensions,
        "dashboard_ready": True,
        **advisory_contract(),
    }
    payload["export_hash"] = stable_hash(payload)
    return payload


def build_all_export_tables() -> dict[str, dict[str, Any]]:
    return {
        INCIDENT_FACT.table_name: build_incident_fact(),
        ESCALATION_FACT.table_name: build_escalation_fact(),
        WATCHLIST_FACT.table_name: build_watchlist_fact(),
        TREND_FACT.table_name: build_trend_fact(),
        CONTINUITY_FACT.table_name: build_continuity_fact(),
        SUMMARY_SNAPSHOT.table_name: build_summary_snapshot(),
        "governance_dimensions": build_dimension_exports(),
    }
