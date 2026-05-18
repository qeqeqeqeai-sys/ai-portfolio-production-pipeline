from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .escalation_history import normalize_escalation
from .hashing import stable_hash
from .incident_history import normalize_incidents
from .watchlist_history import normalize_watchlists

LOG_DIR = Path("logs")
RISK_SUMMARY_PATH = LOG_DIR / "tier3h5_governance_risk_summary.json"
ESCALATION_SUMMARY_PATH = LOG_DIR / "tier3h5_governance_escalation_summary.json"
INCIDENT_SUMMARY_PATH = LOG_DIR / "tier3h5_governance_incident_summary.json"
WATCHLISTS_PATH = LOG_DIR / "tier3h5_governance_watchlists.json"

INCIDENT_HISTORY_PATH = LOG_DIR / "tier3h5_governance_incident_history.json"
ESCALATION_HISTORY_PATH = LOG_DIR / "tier3h5_governance_escalation_history.json"
WATCHLIST_HISTORY_PATH = LOG_DIR / "tier3h5_governance_watchlist_history.json"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _history_status(depth: int) -> str:
    if depth <= 0:
        return "governance_history_initializing"
    if depth < 3:
        return "partial_governance_history_available"
    return "stable_governance_history_available"


def _append_unique(existing: list[dict[str, Any]], incoming: list[dict[str, Any]], hash_field: str) -> list[dict[str, Any]]:
    seen = {item.get(hash_field) for item in existing if isinstance(item, dict)}
    merged = [item for item in existing if isinstance(item, dict)]
    for item in incoming:
        if item.get(hash_field) not in seen:
            merged.append(item)
            seen.add(item.get(hash_field))
    return sorted(merged, key=lambda x: json.dumps(x, sort_keys=True))


def persist_governance_history() -> dict[str, Any]:
    risk = load_json(RISK_SUMMARY_PATH)
    escalation = load_json(ESCALATION_SUMMARY_PATH)
    incidents = load_json(INCIDENT_SUMMARY_PATH)
    watchlists = load_json(WATCHLISTS_PATH)

    incoming_incidents = normalize_incidents(incidents)
    incoming_escalation = [] if not escalation else [normalize_escalation(escalation)]
    incoming_watchlists = normalize_watchlists(watchlists)

    incident_payload = load_json(INCIDENT_HISTORY_PATH)
    escalation_payload = load_json(ESCALATION_HISTORY_PATH)
    watchlist_payload = load_json(WATCHLIST_HISTORY_PATH)

    incident_history = _append_unique(incident_payload.get("history", []), incoming_incidents, "incident_lifecycle_hash")
    escalation_history = _append_unique(escalation_payload.get("history", []), incoming_escalation, "escalation_history_hash")
    watchlist_history = _append_unique(watchlist_payload.get("history", []), incoming_watchlists, "watchlist_evolution_hash")

    incident_out = {
        "phase": "tier3h5_phase4c",
        "history": incident_history,
        "governance_history_depth": len(incident_history),
        "historical_governance_status": _history_status(len(incident_history)),
        "replay_mode": "advisory_only",
        "enforcement_enabled": False,
    }
    incident_out["governance_history_hash"] = stable_hash(incident_out)

    escalation_out = {
        "phase": "tier3h5_phase4c",
        "history": escalation_history,
        "governance_history_depth": len(escalation_history),
        "historical_governance_status": _history_status(len(escalation_history)),
        "replay_mode": "advisory_only",
        "enforcement_enabled": False,
    }
    escalation_out["escalation_history_hash"] = stable_hash(escalation_out)

    watchlist_out = {
        "phase": "tier3h5_phase4c",
        "history": watchlist_history,
        "governance_history_depth": len(watchlist_history),
        "historical_governance_status": _history_status(len(watchlist_history)),
        "replay_mode": "advisory_only",
        "enforcement_enabled": False,
    }
    watchlist_out["watchlist_evolution_hash"] = stable_hash(watchlist_out)

    write_json(INCIDENT_HISTORY_PATH, incident_out)
    write_json(ESCALATION_HISTORY_PATH, escalation_out)
    write_json(WATCHLIST_HISTORY_PATH, watchlist_out)

    return {"risk_summary": risk, "incident_history": incident_out, "escalation_history": escalation_out, "watchlist_history": watchlist_out}
