from __future__ import annotations

from typing import Any

from .contagion_signatures import compute_containment_integrity_checksum


def _b(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))


def compute_containment_integrity(corridors: list[dict[str, Any]]) -> dict[str, Any]:
    edges = sorted((dict(e) for e in corridors), key=lambda x: str(x.get("corridor_id", "")))
    if not edges:
        out = {"containment_integrity_score": 1.0, "containment_weakening_detected": False}
        out["containment_integrity_checksum"] = compute_containment_integrity_checksum(out)
        return out
    vals = [_b(e.get("containment", 0.0)) for e in edges]
    score = _b(sum(vals) / len(vals))
    out = {"containment_integrity_score": score, "containment_weakening_detected": score < 0.45}
    out["containment_integrity_checksum"] = compute_containment_integrity_checksum(out)
    return out
