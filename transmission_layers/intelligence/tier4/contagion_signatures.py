from __future__ import annotations

import hashlib
import json
from typing import Any

EXCLUDED_KEYS = {"timestamp", "runtime_duration", "duration_ms", "duration_seconds", "generated_at"}


def _normalize(value: Any) -> Any:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key in sorted(value.keys(), key=lambda x: str(x)):
            k = str(key)
            if k in EXCLUDED_KEYS:
                continue
            out[k] = _normalize(value[key])
        return out
    if isinstance(value, (list, tuple)):
        return [_normalize(v) for v in value]
    if isinstance(value, set):
        return sorted((_normalize(v) for v in value), key=lambda x: json.dumps(x, sort_keys=True, separators=(",", ":")))
    if isinstance(value, float):
        return round(float(value), 6)
    return value


def _checksum(payload: dict[str, Any]) -> str:
    normalized = _normalize(payload)
    encoded = json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def compute_contagion_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)


def compute_stress_concentration_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)


def compute_stress_amplification_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)


def compute_contagion_boundary_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)


def compute_containment_integrity_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)


def compute_stress_leakage_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)


def compute_propagation_containment_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)


def compute_contagion_signature_checksum(payload: dict[str, Any]) -> str:
    return _checksum(payload)
