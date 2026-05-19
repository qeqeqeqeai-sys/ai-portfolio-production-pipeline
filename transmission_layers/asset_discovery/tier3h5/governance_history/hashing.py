from __future__ import annotations

import hashlib
import json
from typing import Any

HASH_FIELDS = {
    "governance_history_hash",
    "governance_trend_hash",
    "incident_lifecycle_hash",
    "escalation_history_hash",
    "watchlist_evolution_hash",
    "continuity_hash",
    "history_entry_hash",
    "trend_entry_hash",
    "phase4c_summary_hash",
    "explainability_continuity_hash",
    "dashboard_view_hash",
    "snapshot_hash",
}

VOLATILE_HISTORY_FIELDS = {
    "incident_history_id",
    "escalation_history_id",
    "watchlist_history_id",
    "incident_id",
    "incident_hash",
    "escalation_summary_hash",
    "created_at",
    "updated_at",
    "inserted_at",
    "archived_at",
    "archived_at_sgt",
    "timestamp",
    "event_timestamp",
    "ingested_at",
    "auto_id",
    "insertion_order",
}


def canonicalize(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {
            str(k): canonicalize(v)
            for k, v in sorted(payload.items())
            if k not in HASH_FIELDS and k not in VOLATILE_HISTORY_FIELDS
        }
    if isinstance(payload, list):
        normalized = [canonicalize(v) for v in payload]
        return sorted(normalized, key=lambda item: json.dumps(item, sort_keys=True, separators=(",", ":")))
    return payload


def stable_hash(payload: Any) -> str:
    encoded = json.dumps(canonicalize(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
