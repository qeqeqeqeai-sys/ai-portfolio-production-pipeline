from __future__ import annotations

from typing import Any

from .hashing import stable_hash


def incident_key(incident: dict[str, Any]) -> str:
    return "|".join(str(incident.get(k, "")) for k in ("category", "signal", "entity", "severity"))


def normalize_incidents(summary: dict[str, Any]) -> list[dict[str, Any]]:
    incidents = summary.get("incidents", []) if isinstance(summary.get("incidents"), list) else []
    rows = []
    for item in incidents:
        if not isinstance(item, dict):
            continue
        row = {
            "incident_history_id": f"tier3h5-incident-history-{stable_hash(incident_key(item))[:16]}",
            "incident_id": item.get("incident_id"),
            "incident_key": incident_key(item),
            "category": item.get("category", "unknown"),
            "severity": item.get("severity", "informational"),
            "signal": item.get("signal", "unknown"),
            "entity": item.get("entity", "unknown"),
            "incident_hash": item.get("incident_hash") or stable_hash(item),
            "replay_mode": "advisory_only",
            "enforcement_enabled": False,
        }
        row["incident_lifecycle_hash"] = stable_hash(row)
        rows.append(row)
    return sorted(rows, key=lambda x: (x["category"], x["signal"], x["entity"], x["severity"]))
