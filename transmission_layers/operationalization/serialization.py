"""Deterministic payload serialization and checksum primitives (Operationalization O1A)."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def _normalize_key(key: Any) -> str:
    """Convert mapping keys to deterministic, JSON-safe strings."""
    if isinstance(key, str):
        return key
    return f"{type(key).__name__}:{repr(key)}"


def _sort_token(value: Any) -> str:
    """Create a deterministic token used to sort set values."""
    normalized = _normalize_value(value)
    return json.dumps(normalized, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _normalize_value(value: Any) -> Any:
    """Recursively normalize values into deterministic JSON-serializable structures."""
    if isinstance(value, dict):
        return {_normalize_key(k): _normalize_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize_value(item) for item in value]
    if isinstance(value, set):
        return [_normalize_value(item) for item in sorted(value, key=_sort_token)]
    return value


def stable_serialize(payload: dict) -> str:
    """Serialize payload to deterministic ASCII-safe compact JSON."""
    normalized = _normalize_value(payload)
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_checksum(payload: dict, prefix: str = "op") -> str:
    """Return stable checksum token in format: '{prefix}_{first_16_sha256_hex}'."""
    serialized = stable_serialize(payload)
    digest = hashlib.sha256(serialized.encode("ascii")).hexdigest()[:16]
    return f"{prefix}_{digest}"
