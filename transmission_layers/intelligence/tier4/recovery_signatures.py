from __future__ import annotations

import hashlib
import json
from typing import Any

_EXCLUDED_KEYS = {
    "timestamp",
    "runtime_duration",
    "duration_ms",
    "duration_seconds",
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
            if key_str in _EXCLUDED_KEYS:
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


def _checksum(payload: dict[str, Any]) -> str:
    encoded = json.dumps(_normalize_payload(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def compute_recovery_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)


def compute_structural_recovery_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)


def compute_recovery_corridor_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)


def compute_regeneration_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)


def compute_reintegration_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)


def compute_recovery_bottleneck_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)


def compute_recovery_fragmentation_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)


def compute_recovery_signature_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)


def compute_recovery_replay_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)


def compute_recovery_decay_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)
