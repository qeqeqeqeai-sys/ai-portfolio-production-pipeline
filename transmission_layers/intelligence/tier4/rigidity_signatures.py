from __future__ import annotations

import hashlib
import json
from typing import Any

_EXCLUDED_KEYS = {"timestamp", "runtime_duration", "duration_ms", "duration_seconds", "generated_at"}


def _normalize(value: Any) -> Any:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key in sorted(value.keys(), key=lambda k: str(k)):
            key_str = str(key)
            if key_str in _EXCLUDED_KEYS:
                continue
            out[key_str] = _normalize(value[key])
        return out
    if isinstance(value, (list, tuple)):
        return [_normalize(v) for v in value]
    if isinstance(value, set):
        return sorted((_normalize(v) for v in value), key=lambda x: json.dumps(x, sort_keys=True, separators=(",", ":")))
    if isinstance(value, float):
        return round(value, 6)
    return value


def _checksum(payload: dict[str, Any]) -> str:
    encoded = json.dumps(_normalize(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def compute_rigidity_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)


def compute_structural_rigidity_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)


def compute_adaptation_constraint_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)


def compute_resilience_saturation_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)


def compute_flexibility_collapse_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)


def compute_rigidity_cascade_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)


def compute_reintegration_resistance_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)


def compute_adaptation_exhaustion_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)


def compute_rigidity_signature_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)
