from __future__ import annotations

import hashlib
import json
from typing import Any


def _round_for_checksum(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, list):
        return [_round_for_checksum(v) for v in value]
    if isinstance(value, dict):
        return {k: _round_for_checksum(value[k]) for k in sorted(value)}
    return value


def federation_temporal_checksum(payload: dict[str, Any]) -> str:
    clean = _round_for_checksum(payload)
    encoded = json.dumps(clean, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]


def federation_signature_stability(signatures: list[str]) -> float:
    if not signatures:
        return 0.0
    unique = len(set(sorted(signatures)))
    return max(0.0, min(1.0, 1.0 - ((unique - 1) / max(1, len(signatures) - 1))))
