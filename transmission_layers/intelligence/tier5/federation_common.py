from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable


def clamp_score(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def mean_bounded(values: Iterable[float]) -> float:
    seq = [clamp_score(v) for v in values]
    if not seq:
        return 0.0
    return clamp_score(sum(seq) / len(seq))


def weighted_bounded_score(pairs: Iterable[tuple[float, float]]) -> float:
    norm = [(clamp_score(v), max(0.0, float(w))) for v, w in pairs]
    den = sum(w for _, w in norm)
    if den <= 0.0:
        return 0.0
    return clamp_score(sum(v * w for v, w in norm) / den)


def canonical_checksum(payload: dict[str, Any], *, prefix: str) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"
