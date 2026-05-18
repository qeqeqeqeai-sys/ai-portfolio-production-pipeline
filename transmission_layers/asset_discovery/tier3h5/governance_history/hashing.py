from __future__ import annotations

import hashlib
import json
from typing import Any

HASH_FIELDS = [
    "governance_history_hash",
    "governance_trend_hash",
    "incident_lifecycle_hash",
    "escalation_history_hash",
    "watchlist_evolution_hash",
    "continuity_hash",
    "history_entry_hash",
    "trend_entry_hash",
]


def canonicalize(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {str(k): canonicalize(v) for k, v in sorted(payload.items()) if k not in HASH_FIELDS}
    if isinstance(payload, list):
        return [canonicalize(v) for v in payload]
    return payload


def stable_hash(payload: Any) -> str:
    encoded = json.dumps(canonicalize(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
