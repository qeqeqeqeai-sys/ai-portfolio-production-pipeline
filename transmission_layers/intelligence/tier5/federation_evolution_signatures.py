from __future__ import annotations

import hashlib
import json
from typing import Any


def _normalize_for_checksum(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, list):
        return [_normalize_for_checksum(v) for v in value]
    if isinstance(value, dict):
        return {k: _normalize_for_checksum(value[k]) for k in sorted(value)}
    return value


def federation_evolution_checksum(payload: dict[str, Any], *, prefix: str = "") -> str:
    clean = _normalize_for_checksum(payload)
    encoded = json.dumps(clean, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}" if prefix else digest
