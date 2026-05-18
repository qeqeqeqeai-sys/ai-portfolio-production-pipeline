from __future__ import annotations

from typing import Any

from .hashing import stable_hash


def explain_history(summary: dict[str, Any], trend: dict[str, Any], continuity: dict[str, Any]) -> dict[str, Any]:
    incident_count = int(summary.get("persistent_incident_count", 0) or 0) + int(summary.get("recurring_incident_count", 0) or 0) + int(summary.get("transient_incident_count", 0) or 0)
    out = {
        "phase": "tier3h5_phase4c",
        "persistence_explanation": {
            "status": summary.get("historical_governance_status", "governance_history_initializing"),
            "governance_history_depth": summary.get("governance_history_depth", 0),
            "source": "persisted_governance_history_only",
        },
        "trend_explanation": {
            "governance_trend_status": trend.get("governance_trend_status", "insufficient_history"),
            "escalation_trend_status": trend.get("escalation_trend_status", "insufficient_history"),
        },
        "continuity_explanation": {
            "historical_continuity_status": continuity.get("historical_continuity_status", "insufficient_governance_history"),
            "classification_basis": "archived_summaries_and_persisted_history",
        },
        "lifecycle_explanation": {
            "incident_lifecycle_count": incident_count,
            "mutation_performed": False,
        },
        "replay_mode": "advisory_only",
        "enforcement_enabled": False,
    }
    out["explainability_continuity_hash"] = stable_hash(out)
    return out
