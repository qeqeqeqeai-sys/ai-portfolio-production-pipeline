"""B3 certified snapshot envelope and checksum helpers."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json

FORBIDDEN_CAPABILITY_CONTRACT = {
    "live_fetching": "disallowed",
    "database_writes": "disallowed",
    "dashboard_mutation": "disallowed",
    "trading": "disallowed",
    "prediction": "disallowed",
    "target_prices": "disallowed",
    "portfolio_allocation": "disallowed",
    "optimization": "disallowed",
    "autonomous_notifications": "disallowed",
    "adaptive_learning": "disallowed",
    "unrestricted_llm_reasoning": "disallowed",
}


def stable_b3_checksum(payload: object) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_b3_certified_snapshot_envelope(parts: dict) -> dict:
    envelope = deepcopy(parts)
    envelope["forbidden_capability_contract"] = deepcopy(FORBIDDEN_CAPABILITY_CONTRACT)
    envelope["persistence_ready"] = envelope.get("b3_decision") in {"CERTIFIED_SNAPSHOT_READY", "DEGRADED_SNAPSHOT_READY"}
    envelope["deterministic_checksum"] = stable_b3_checksum(envelope)
    return envelope
