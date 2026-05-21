from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

from .federation_common import clamp_score


EXCLUDED_CHECKSUM_KEYS = {"timestamp", "timestamps", "runtime_duration", "duration", "elapsed", "elapsed_ms"}


def _normalize(value: Any) -> Any:
    if isinstance(value, float):
        return round(clamp_score(value) if 0.0 <= value <= 1.0 else value, 6)
    if isinstance(value, list):
        return [_normalize(v) for v in value]
    if isinstance(value, tuple):
        return [_normalize(v) for v in value]
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for k in sorted(value):
            if k in EXCLUDED_CHECKSUM_KEYS:
                continue
            cleaned[str(k)] = _normalize(value[k])
        return cleaned
    if isinstance(value, set):
        return [_normalize(v) for v in sorted(value, key=lambda x: str(x))]
    return value


def stable_checksum(payload: dict[str, Any], *, prefix: str) -> str:
    normalized = _normalize(deepcopy(payload))
    encoded = json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def deterministic_replay_stability(payload: dict[str, Any], *, runs: int = 3) -> tuple[float, str]:
    checksums = [stable_checksum(payload, prefix="det") for _ in range(max(1, runs))]
    stable = 1.0 if len(set(checksums)) == 1 else 0.0
    return stable, checksums[0]
