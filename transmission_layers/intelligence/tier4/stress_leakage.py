from __future__ import annotations

from typing import Any

from .contagion_signatures import compute_stress_leakage_checksum


def _b(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))


def compute_stress_leakage(corridors: list[dict[str, Any]]) -> dict[str, Any]:
    edges = sorted((dict(e) for e in corridors), key=lambda x: str(x.get("corridor_id", "")))
    if not edges:
        out = {"stress_leakage_score": 0.0, "containment_breach_score": 0.0, "stress_leakage_detected": False, "containment_breach_detected": False}
        out["stress_leakage_checksum"] = compute_stress_leakage_checksum(out)
        return out
    leaks = [_b(e.get("leakage", max(0.0, _b(e.get("exit_stress", 0.0)) - _b(e.get("containment", 0.0))))) for e in edges]
    score = _b(sum(leaks) / len(leaks))
    breach_score = _b(sum(1 for x in leaks if x >= 0.4) / len(leaks))
    out = {
        "stress_leakage_score": score,
        "containment_breach_score": breach_score,
        "stress_leakage_detected": score >= 0.25,
        "containment_breach_detected": breach_score >= 0.3,
    }
    out["stress_leakage_checksum"] = compute_stress_leakage_checksum(out)
    return out
