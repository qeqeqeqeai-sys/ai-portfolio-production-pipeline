from __future__ import annotations

from typing import Any


def _b(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 6)


def compute_survivability_metrics(fragility: dict[str, Any], threshold_eval: dict[str, Any]) -> dict[str, Any]:
    system_fragility = _b(float(fragility.get("system_fragility_score", 0.0)))
    breaches = int(threshold_eval.get("threshold_breach_count", 0))
    nodes = max(1, int(fragility.get("node_count", 0)))
    breach_ratio = _b(breaches / nodes)
    survivability = _b(1.0 - ((system_fragility * 0.7) + (breach_ratio * 0.3)))
    corridor_failure = _b((breach_ratio * 0.6) + (system_fragility * 0.4))
    irreversible_cascade = corridor_failure >= 0.7 and system_fragility >= 0.7
    return {
        "survivability_score": survivability,
        "corridor_failure_diagnostic": corridor_failure,
        "cascade_irreversibility_detected": irreversible_cascade,
    }
