from __future__ import annotations

from typing import Any


def _b(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 6)


def evaluate_failure_thresholds(fragility: dict[str, Any], threshold: float = 0.65) -> dict[str, Any]:
    t = _b(threshold)
    ranked = list(fragility.get("node_fragility_ranking", []))
    breached = [r for r in ranked if _b(float(r.get("fragility_score", 0.0))) >= t]
    return {
        "failure_threshold": t,
        "threshold_breaches": sorted(str(r.get("node_id", "")) for r in breached),
        "threshold_breach_count": len(breached),
        "system_threshold_breached": _b(float(fragility.get("system_fragility_score", 0.0))) >= t,
    }
