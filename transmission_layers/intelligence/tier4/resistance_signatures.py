from __future__ import annotations

import hashlib
import json
from typing import Any

EXCLUDED_KEYS = {"timestamp", "runtime_duration", "duration_ms", "duration_seconds", "generated_at"}


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
        return sorted((_normalize_payload(v) for v in value), key=lambda x: json.dumps(x, sort_keys=True, separators=(",", ":")))
    if isinstance(value, float):
        return round(float(value), 6)
    return value


def _checksum(payload: dict[str, Any]) -> str:
    normalized = _normalize_payload(payload)
    encoded = json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def compute_capacity_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)


def compute_pressure_resistance_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)


def compute_exhaustion_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)


def compute_saturation_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)


def compute_resistance_replay_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)


def compute_resistance_signature_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)
