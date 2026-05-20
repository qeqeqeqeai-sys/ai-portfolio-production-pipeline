from __future__ import annotations

from typing import Any


def _bound01(value: float) -> float:
    return max(0.0, min(1.0, round(float(value), 6)))


def compute_survivability_metrics(fragility: dict[str, Any], threshold_eval: dict[str, Any]) -> dict[str, Any]:
    system_fragility = _bound01(float(fragility.get("system_fragility_score", 0.0)))
    breach_ratio = _bound01(float(threshold_eval.get("threshold_breach_ratio", 0.0)))
    if breach_ratio == 0.0:
        breaches = int(threshold_eval.get("threshold_breach_count", 0))
        nodes = max(1, int(fragility.get("node_count", 0)))
        breach_ratio = _bound01(breaches / nodes)

    survivability = _bound01(1.0 - ((system_fragility * 0.7) + (breach_ratio * 0.3)))
    corridor_failure = _bound01((breach_ratio * 0.6) + (system_fragility * 0.4))
    irreversible_cascade = corridor_failure >= 0.7 and system_fragility >= 0.7
    margin_to_failure = _bound01(1.0 - corridor_failure)

    return {
        "survivability_score": survivability,
        "corridor_failure_diagnostic": corridor_failure,
        "cascade_irreversibility_detected": irreversible_cascade,
        "failure_margin": margin_to_failure,
        "system_stability_band": "high" if survivability >= 0.67 else "moderate" if survivability >= 0.34 else "low",
    }
