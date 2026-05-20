from __future__ import annotations

import hashlib
import json
from typing import Any


def _normalize(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, list):
        return [_normalize(v) for v in value]
    if isinstance(value, tuple):
        return [_normalize(v) for v in value]
    if isinstance(value, dict):
        return {k: _normalize(value[k]) for k in sorted(value)}
    return value


def observability_checksum(payload: dict[str, Any], prefix: str) -> str:
    encoded = json.dumps(_normalize(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"
