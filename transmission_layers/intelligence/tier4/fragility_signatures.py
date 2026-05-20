from __future__ import annotations

import hashlib
import json
from typing import Any

EXCLUDED_KEYS = {
    "timestamp",
    "runtime_duration",
    "duration_ms",
    "duration_seconds",
    "environment",
    "host",
    "pid",
}


def _round_float(value: Any) -> float:
    try:
        return round(float(value), 6)
    except (TypeError, ValueError):
        return 0.0


def _normalize_payload(value: Any) -> Any:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key in sorted(value.keys(), key=lambda k: str(k)):
            key_str = str(key)
            if key_str in EXCLUDED_KEYS:
                continue
            out[key_str] = _normalize_payload(value[key])
        return out
    if isinstance(value, (list, tuple)):
        return [_normalize_payload(v) for v in value]
    if isinstance(value, set):
        return sorted(_normalize_payload(v) for v in value)
    if isinstance(value, float):
        return _round_float(value)
    return value


def compute_fragility_checksum(payload: dict[str, Any]) -> str:
    normalized = _normalize_payload(payload)
    encoded = json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def compute_fragility_replay_checksum(payload: dict[str, Any]) -> str:
    return compute_fragility_checksum(payload)
