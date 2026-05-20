from __future__ import annotations

import hashlib
import json
from typing import Any


def _round_float(value: Any) -> float:
    try:
        return round(float(value), 6)
    except (TypeError, ValueError):
        return 0.0


def _normalize_payload(value: Any) -> Any:
    if isinstance(value, dict):
        out = {}
        for key in sorted(value.keys(), key=lambda k: str(k)):
            key_str = str(key)
            if key_str in {"timestamp", "runtime_duration", "duration_ms", "duration_seconds", "environment", "host", "pid"}:
                continue
            out[key_str] = _normalize_payload(value[key])
        return out
    if isinstance(value, list):
        return [_normalize_payload(v) for v in value]
    if isinstance(value, tuple):
        return [_normalize_payload(v) for v in value]
    if isinstance(value, set):
        return sorted(_normalize_payload(v) for v in value)
    if isinstance(value, float):
        return _round_float(value)
    return value


def compute_response_checksum(payload: dict[str, Any]) -> str:
    normalized = _normalize_payload(payload)
    return hashlib.sha256(json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def compute_response_replay_checksum(payload: dict[str, Any]) -> str:
    return compute_response_checksum(payload)


def compute_response_effectiveness_checksum(payload: dict[str, Any]) -> str:
    return compute_response_checksum(payload)


def compute_response_signature_checksum(payload: dict[str, Any]) -> str:
    return compute_response_checksum(payload)
