from __future__ import annotations

from typing import Any


def validate_dashboard_readiness(dashboards: dict[str, dict[str, Any]]) -> dict[str, Any]:
    statuses = sorted(str(v.get("dashboard_history_status", "insufficient_dashboard_history")) for v in dashboards.values())
    ready = all(v.get("replay_mode") == "advisory_only" and v.get("enforcement_enabled") is False for v in dashboards.values()) and bool(dashboards)
    return {
        "dashboard_ready": ready,
        "dashboard_export_status": "ready" if ready else "partial",
        "dashboard_history_statuses": statuses,
        "governance_history_ready": any(s in {"stable_dashboard_history_available", "partial_dashboard_history_available", "dashboard_history_initializing"} for s in statuses),
    }
