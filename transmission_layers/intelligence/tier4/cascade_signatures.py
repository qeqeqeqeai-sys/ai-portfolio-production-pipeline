from __future__ import annotations

import hashlib
import json
from typing import Any

_EXCLUDED_KEYS = {"timestamp", "runtime_duration", "duration_ms", "duration_seconds", "generated_at"}


def _bound01(value: float) -> float:
    return max(0.0, min(1.0, round(float(value), 6)))


def _normalize(value: Any) -> Any:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key in sorted(value.keys(), key=lambda k: str(k)):
            key_s = str(key)
            if key_s in _EXCLUDED_KEYS:
                continue
            out[key_s] = _normalize(value[key])
        return out
    if isinstance(value, (list, tuple)):
        return [_normalize(v) for v in value]
    if isinstance(value, set):
        return sorted((_normalize(v) for v in value), key=lambda x: json.dumps(x, sort_keys=True, separators=(",", ":")))
    if isinstance(value, float):
        return round(value, 6)
    return value


def deterministic_checksum(payload: dict[str, Any]) -> str:
    encoded = json.dumps(_normalize(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def compute_cascade_signature_checksum(payload: dict[str, Any]) -> str:
    return deterministic_checksum(payload)


def compute_cascade_checksum(payload: dict[str, Any]) -> str:
    return deterministic_checksum(payload)


def compute_structural_criticality_checksum(payload: dict[str, Any]) -> str:
    return deterministic_checksum(payload)


def compute_systemic_cascade_checksum(payload: dict[str, Any]) -> str:
    return deterministic_checksum(payload)


def compute_cascade_corridor_checksum(payload: dict[str, Any]) -> str:
    return deterministic_checksum(payload)


def compute_bottleneck_checksum(payload: dict[str, Any]) -> str:
    return deterministic_checksum(payload)


def compute_dependency_concentration_checksum(payload: dict[str, Any]) -> str:
    return deterministic_checksum(payload)


def compute_cascade_boundary_checksum(payload: dict[str, Any]) -> str:
    return deterministic_checksum(payload)
