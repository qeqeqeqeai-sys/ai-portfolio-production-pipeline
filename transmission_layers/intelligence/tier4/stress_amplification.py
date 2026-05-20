from __future__ import annotations

from typing import Any

from .contagion_signatures import compute_stress_amplification_checksum


def _b(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))


def compute_stress_amplification(corridors: list[dict[str, Any]]) -> dict[str, Any]:
    edges = sorted((dict(e) for e in corridors), key=lambda x: str(x.get("corridor_id", "")))
    if not edges:
        out = {"stress_amplification_score": 0.0, "stress_amplifier_detected": False}
        out["stress_amplification_checksum"] = compute_stress_amplification_checksum(out)
        return out
    deltas = [_b(e.get("exit_stress", 0.0)) - _b(e.get("entry_stress", 0.0)) for e in edges]
    positive = [d for d in deltas if d > 0]
    score = _b(sum(positive) / len(edges) if positive else 0.0)
    out = {"stress_amplification_score": score, "stress_amplifier_detected": score >= 0.25}
    out["stress_amplification_checksum"] = compute_stress_amplification_checksum(out)
    return out
