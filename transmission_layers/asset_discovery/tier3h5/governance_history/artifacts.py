from __future__ import annotations

from typing import Any

from .continuity import classify_historical_continuity
from .explainability import explain_history
from .hashing import stable_hash
from .persistence import LOG_DIR, load_json, persist_governance_history, write_json
from .trend_analytics import analyze_governance_trends

HISTORY_SUMMARY_PATH = LOG_DIR / "tier3h5_governance_history_summary.json"
TREND_SUMMARY_PATH = LOG_DIR / "tier3h5_governance_trend_summary.json"
PHASE4C_SUMMARY_PATH = LOG_DIR / "tier3h5_phase4c_governance_history_summary.json"
CONTINUITY_HISTORY_PATH = LOG_DIR / "tier3h5_governance_continuity_history.json"
TREND_HISTORY_PATH = LOG_DIR / "tier3h5_governance_trend_history.json"
EXPLAINABILITY_PATH = LOG_DIR / "tier3h5_governance_history_explainability.json"


def history_availability(depth: int) -> str:
    if depth <= 0:
        return "governance_history_initializing"
    if depth < 3:
        return "partial_governance_history_available"
    return "stable_governance_history_available"


def build_history_summary(persisted: dict[str, Any], trend: dict[str, Any], continuity: dict[str, Any]) -> dict[str, Any]:
    depth = int(continuity.get("governance_history_depth", 0) or 0)
    summary = {
        "phase": "tier3h5_phase4c",
        "historical_governance_status": history_availability(depth),
        "governance_trend_status": trend.get("governance_trend_status", "insufficient_history"),
        "persistent_incident_count": continuity.get("persistent_incident_count", 0),
        "recurring_incident_count": continuity.get("recurring_incident_count", 0),
        "transient_incident_count": continuity.get("transient_incident_count", 0),
        "escalation_trend_status": trend.get("escalation_trend_status", "insufficient_history"),
        "replay_stability_trend": trend.get("replay_stability_trend", "insufficient_history"),
        "lineage_stability_trend": trend.get("lineage_stability_trend", "insufficient_history"),
        "governance_history_depth": depth,
        "historical_continuity_status": continuity.get("historical_continuity_status", "insufficient_governance_history"),
        "governance_history_hash": persisted["incident_history"].get("governance_history_hash"),
        "governance_trend_hash": trend.get("governance_trend_hash"),
        "escalation_history_hash": persisted["escalation_history"].get("escalation_history_hash"),
        "watchlist_evolution_hash": persisted["watchlist_history"].get("watchlist_evolution_hash"),
        "continuity_hash": continuity.get("continuity_hash"),
        "replay_mode": "advisory_only",
        "enforcement_enabled": False,
        "canonical_override_enabled": False,
        "scoring_mutation_enabled": False,
        "confidence_mutation_enabled": False,
        "propagation_mutation_enabled": False,
    }
    summary["phase4c_summary_hash"] = stable_hash(summary)
    return summary


def run_phase4c_governance_history() -> dict[str, Any]:
    persisted = persist_governance_history()
    incident_history = persisted["incident_history"].get("history", [])
    escalation_history = persisted["escalation_history"].get("history", [])
    trend = analyze_governance_trends(incident_history, escalation_history)
    continuity = classify_historical_continuity(incident_history)
    summary = build_history_summary(persisted, trend, continuity)
    explanation = explain_history(summary, trend, continuity)

    prior_trends = [item for item in load_json(TREND_HISTORY_PATH).get("history", []) if isinstance(item, dict)]
    prior_continuity = [item for item in load_json(CONTINUITY_HISTORY_PATH).get("history", []) if isinstance(item, dict)]
    trend_hashes = {item.get("governance_trend_hash") for item in prior_trends}
    continuity_hashes = {item.get("continuity_hash") for item in prior_continuity}
    trend_entries = prior_trends + ([] if trend.get("governance_trend_hash") in trend_hashes else [trend])
    continuity_entries = prior_continuity + ([] if continuity.get("continuity_hash") in continuity_hashes else [continuity])
    trend_history = {"phase": "tier3h5_phase4c", "history": trend_entries, "replay_mode": "advisory_only", "enforcement_enabled": False}
    trend_history["governance_trend_hash"] = stable_hash(trend_history)
    continuity_history = {"phase": "tier3h5_phase4c", "history": continuity_entries, "replay_mode": "advisory_only", "enforcement_enabled": False}
    continuity_history["continuity_hash"] = stable_hash(continuity_history)

    write_json(HISTORY_SUMMARY_PATH, summary)
    write_json(TREND_SUMMARY_PATH, trend)
    write_json(PHASE4C_SUMMARY_PATH, summary)
    write_json(TREND_HISTORY_PATH, trend_history)
    write_json(CONTINUITY_HISTORY_PATH, continuity_history)
    write_json(EXPLAINABILITY_PATH, explanation)

    from transmission_layers.asset_discovery.tier3h5.governance_query.dashboard_views import write_dashboard_artifacts

    dashboard_views = write_dashboard_artifacts()
    return {"history_summary": summary, "trend_summary": trend, "continuity_summary": continuity, "explainability": explanation, "dashboard_views": dashboard_views, **persisted}


if __name__ == "__main__":
    run_phase4c_governance_history()
