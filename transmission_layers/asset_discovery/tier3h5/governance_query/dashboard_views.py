from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from transmission_layers.asset_discovery.tier3h5.governance_history.artifacts import CONTINUITY_HISTORY_PATH, HISTORY_SUMMARY_PATH, TREND_HISTORY_PATH, TREND_SUMMARY_PATH
from transmission_layers.asset_discovery.tier3h5.governance_history.hashing import stable_hash
from transmission_layers.asset_discovery.tier3h5.governance_history.persistence import (
    ESCALATION_HISTORY_PATH,
    INCIDENT_HISTORY_PATH,
    LOG_DIR,
    WATCHLIST_HISTORY_PATH,
    load_json,
)

from .base import bounded_window, history_rows, stable_sort
from .serialization import advisory_contract, write_stable_json

DASHBOARD_GOVERNANCE_SUMMARY_PATH = LOG_DIR / "tier3h5_dashboard_governance_summary.json"
DASHBOARD_GOVERNANCE_TRENDS_PATH = LOG_DIR / "tier3h5_dashboard_governance_trends.json"
DASHBOARD_WATCHLIST_SUMMARY_PATH = LOG_DIR / "tier3h5_dashboard_watchlist_summary.json"
DASHBOARD_CONTINUITY_SUMMARY_PATH = LOG_DIR / "tier3h5_dashboard_continuity_summary.json"
DASHBOARD_ESCALATION_SUMMARY_PATH = LOG_DIR / "tier3h5_dashboard_escalation_summary.json"
DASHBOARD_OPERATIONAL_SUMMARY_PATH = LOG_DIR / "tier3h5_dashboard_operational_summary.json"
DASHBOARD_PATHS = (
    DASHBOARD_GOVERNANCE_SUMMARY_PATH,
    DASHBOARD_GOVERNANCE_TRENDS_PATH,
    DASHBOARD_WATCHLIST_SUMMARY_PATH,
    DASHBOARD_CONTINUITY_SUMMARY_PATH,
    DASHBOARD_ESCALATION_SUMMARY_PATH,
    DASHBOARD_OPERATIONAL_SUMMARY_PATH,
)

UNRESOLVED_SEVERITIES = {"governance_risk", "governance_review_recommended", "critical_governance_instability"}
DOMAIN_MAP = {
    "replay_governance_incident": "replay_instability_totals",
    "lineage_integrity_incident": "lineage_instability_totals",
    "normalization_governance_incident": "normalization_drift_totals",
    "provenance_governance_incident": "provenance_degradation_totals",
    "cross_registry_governance_incident": "cross_registry_instability_totals",
}


def dashboard_history_status(depth: int) -> str:
    if depth <= 0:
        return "insufficient_dashboard_history"
    if depth == 1:
        return "dashboard_history_initializing"
    if depth < 3:
        return "partial_dashboard_history_available"
    return "stable_dashboard_history_available"


def _latest_generated_at(rows: list[dict[str, Any]]) -> str:
    values = [str(row.get("run_date_sgt") or row.get("run_date") or row.get("archived_at_sgt")) for row in rows if row.get("run_date_sgt") or row.get("run_date") or row.get("archived_at_sgt")]
    return max(values) if values else "deterministic_replay"


def _counter(rows: list[dict[str, Any]], field: str, default: str = "unknown") -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(field, default) or default) for row in rows).items()))


def _base(kind: str, rows: list[dict[str, Any]], window: int) -> dict[str, Any]:
    depth = len(rows)
    return {
        "phase": "tier3h5_phase4d",
        "dashboard_kind": kind,
        "dashboard_generated_at": _latest_generated_at(rows),
        "dashboard_history_status": dashboard_history_status(depth),
        "governance_history_depth": depth,
        "query_window": min(window, depth),
        **advisory_contract(),
    }


def build_governance_summary_view(window: int = 100) -> dict[str, Any]:
    incidents = bounded_window(history_rows(INCIDENT_HISTORY_PATH), window)
    base = _base("governance_summary", incidents, window)
    domain_counts = _counter(incidents, "category")
    severity_counts = _counter(incidents, "severity")
    unresolved = [row for row in incidents if row.get("severity") in UNRESOLVED_SEVERITIES]
    payload = {
        **base,
        "governance_incident_totals": domain_counts,
        "severity_distribution": severity_counts,
        "governance_domain_distribution": domain_counts,
        "unresolved_governance_totals": len(unresolved),
        "registry_source_distribution": _counter(incidents, "registry_source"),
        "run_date_sgt_distribution": _counter(incidents, "run_date_sgt", "undated"),
    }
    for category, field in DOMAIN_MAP.items():
        payload[field] = domain_counts.get(category, 0)
    payload["dashboard_view_hash"] = stable_hash(payload)
    return payload


def build_trend_summary_view(window: int = 100) -> dict[str, Any]:
    rows = bounded_window(history_rows(TREND_HISTORY_PATH) or ([load_json(TREND_SUMMARY_PATH)] if load_json(TREND_SUMMARY_PATH) else []), window)
    payload = {
        **_base("governance_trends", rows, window),
        "governance_trend_distribution": _counter(rows, "governance_trend_status", "insufficient_history"),
        "escalation_trend_distribution": _counter(rows, "escalation_trend_status", "insufficient_history"),
        "replay_instability_timeline": [{"run_date_sgt": row.get("run_date_sgt", "undated"), "replay_stability_trend": row.get("replay_stability_trend", "insufficient_history")} for row in stable_sort(rows)],
        "lineage_degradation_summary": _counter(rows, "lineage_stability_trend", "insufficient_history"),
        "normalization_drift_summary": _counter(rows, "normalization_drift_trend", "insufficient_history"),
        "provenance_degradation_summary": _counter(rows, "provenance_quality_trend", "insufficient_history"),
    }
    payload["dashboard_view_hash"] = stable_hash(payload)
    return payload


def build_watchlist_summary_view(window: int = 100) -> dict[str, Any]:
    rows = bounded_window(history_rows(WATCHLIST_HISTORY_PATH), window)
    payload = {
        **_base("watchlist_summary", rows, window),
        "watchlist_persistence_summary": _counter(rows, "watchlist_name"),
        "watchlist_item_total": sum(int(row.get("watchlist_count", 0) or 0) for row in rows),
    }
    payload["dashboard_view_hash"] = stable_hash(payload)
    return payload


def build_continuity_summary_view(window: int = 100) -> dict[str, Any]:
    rows = bounded_window(history_rows(CONTINUITY_HISTORY_PATH) or ([load_json(HISTORY_SUMMARY_PATH)] if load_json(HISTORY_SUMMARY_PATH) else []), window)
    payload = {
        **_base("continuity_summary", rows, window),
        "continuity_distribution": _counter(rows, "historical_continuity_status", "insufficient_governance_history"),
        "continuity_lifecycle_distribution": _counter(rows, "continuity_status", "unspecified"),
        "persistent_incident_total": sum(int(row.get("persistent_incident_count", 0) or 0) for row in rows),
        "recurring_incident_total": sum(int(row.get("recurring_incident_count", 0) or 0) for row in rows),
        "transient_incident_total": sum(int(row.get("transient_incident_count", 0) or 0) for row in rows),
    }
    payload["dashboard_view_hash"] = stable_hash(payload)
    return payload


def build_escalation_summary_view(window: int = 100) -> dict[str, Any]:
    rows = bounded_window(history_rows(ESCALATION_HISTORY_PATH), window)
    payload = {
        **_base("escalation_summary", rows, window),
        "escalation_totals": _counter(rows, "escalation_status", "no_escalation"),
        "governance_review_recommended_total": sum(1 for row in rows if row.get("governance_review_recommended") is True),
    }
    payload["dashboard_view_hash"] = stable_hash(payload)
    return payload


def build_operational_summary_view(window: int = 100) -> dict[str, Any]:
    governance = build_governance_summary_view(window)
    trends = build_trend_summary_view(window)
    continuity = build_continuity_summary_view(window)
    escalation = build_escalation_summary_view(window)
    rows = [{"run_date_sgt": governance["dashboard_generated_at"]}]
    payload = {
        **_base("operational_summary", rows, window),
        "governance_history_depth": governance["governance_history_depth"],
        "governance_incident_totals": governance["governance_incident_totals"],
        "escalation_totals": escalation["escalation_totals"],
        "continuity_distribution": continuity["continuity_distribution"],
        "governance_trend_distribution": trends["governance_trend_distribution"],
        "unresolved_governance_totals": governance["unresolved_governance_totals"],
        "replay_instability_totals": governance["replay_instability_totals"],
        "lineage_instability_totals": governance["lineage_instability_totals"],
        "normalization_drift_totals": governance["normalization_drift_totals"],
        "provenance_degradation_totals": governance["provenance_degradation_totals"],
        "cross_registry_instability_totals": governance["cross_registry_instability_totals"],
    }
    payload["dashboard_view_hash"] = stable_hash(payload)
    return payload


def build_dashboard_views(window: int = 100) -> dict[str, dict[str, Any]]:
    return {
        "governance_summary": build_governance_summary_view(window),
        "governance_trends": build_trend_summary_view(window),
        "watchlist_summary": build_watchlist_summary_view(window),
        "continuity_summary": build_continuity_summary_view(window),
        "escalation_summary": build_escalation_summary_view(window),
        "operational_summary": build_operational_summary_view(window),
    }


def write_dashboard_artifacts(window: int = 100) -> dict[str, dict[str, Any]]:
    views = build_dashboard_views(window)
    path_map: dict[Path, dict[str, Any]] = {
        DASHBOARD_GOVERNANCE_SUMMARY_PATH: views["governance_summary"],
        DASHBOARD_GOVERNANCE_TRENDS_PATH: views["governance_trends"],
        DASHBOARD_WATCHLIST_SUMMARY_PATH: views["watchlist_summary"],
        DASHBOARD_CONTINUITY_SUMMARY_PATH: views["continuity_summary"],
        DASHBOARD_ESCALATION_SUMMARY_PATH: views["escalation_summary"],
        DASHBOARD_OPERATIONAL_SUMMARY_PATH: views["operational_summary"],
    }
    for path, payload in path_map.items():
        write_stable_json(path, payload)
    return views
