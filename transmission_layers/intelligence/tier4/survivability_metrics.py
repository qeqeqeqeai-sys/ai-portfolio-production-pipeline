from __future__ import annotations

from typing import Any

from .fragility_signatures import compute_survivability_checksum


def _bound01(value: float) -> float:
    return max(0.0, min(1.0, round(float(value), 6)))


def compute_survivability_metrics(fragility: dict[str, Any], threshold_eval: dict[str, Any]) -> dict[str, Any]:
    system_fragility = _bound01(float(fragility.get("system_fragility_score", 0.0)))
    threshold_ratio = _bound01(float(threshold_eval.get("threshold_breach_ratio", 0.0)))
    survivability = _bound01(1.0 - ((system_fragility * 0.7) + (threshold_ratio * 0.3)))
    corridor_fragility = _bound01((threshold_ratio * 0.6) + (system_fragility * 0.4))
    irreversible_cascade = corridor_fragility >= 0.7 and system_fragility >= 0.7
    out = {
        "survivability_score": survivability,
        "structural_survivability_score": survivability,
        "corridor_fragility_diagnostic": corridor_fragility,
        "corridor_failure_diagnostic": corridor_fragility,
        "cascade_irreversibility_detected": irreversible_cascade,
        "failure_margin": _bound01(1.0 - corridor_fragility),
        "system_stability_band": "high" if survivability >= 0.67 else "moderate" if survivability >= 0.34 else "low",
    }
    out["survivability_checksum"] = compute_survivability_checksum(out)
    return out
