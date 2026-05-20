from __future__ import annotations

from typing import Any

from .transition_signatures import compute_fragmentation_checksum


def _b(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))


def compute_fragmentation_diagnostics(corridors: list[dict[str, Any]]) -> dict[str, Any]:
    edges = sorted((dict(c) for c in corridors), key=lambda x: (str(x.get("from", "")), str(x.get("to", ""))))
    if not edges:
        out = {"fragmentation_score": 0.0, "fragmentation_detected": False}
        out["fragmentation_checksum"] = compute_fragmentation_checksum(out)
        return out
    penalties = [_b((float(e.get("suppression", 0.0)) * 0.6) + (float(e.get("stress", 0.0)) * 0.4)) for e in edges]
    score = _b(sum(penalties) / len(penalties))
    out = {"fragmentation_score": score, "fragmentation_detected": score >= 0.5}
    out["fragmentation_checksum"] = compute_fragmentation_checksum(out)
    return out
