from __future__ import annotations

from typing import Any


def _bound01(value: float) -> float:
    return max(0.0, min(1.0, round(float(value), 6)))


def _classify(score: float, threshold: float) -> str:
    if score >= threshold + 0.2:
        return "critical"
    if score >= threshold:
        return "at_risk"
    return "stable"


def evaluate_failure_thresholds(fragility: dict[str, Any], threshold: float = 0.65) -> dict[str, Any]:
    t = _bound01(threshold)
    ranked = list(fragility.get("node_fragility_ranking", []))
    node_statuses = sorted(
        [
            {
                "node_id": str(r.get("node_id", "")),
                "fragility_score": _bound01(float(r.get("fragility_score", 0.0))),
                "status": _classify(_bound01(float(r.get("fragility_score", 0.0))), t),
            }
            for r in ranked
        ],
        key=lambda x: x["node_id"],
    )
    breached = sorted(n["node_id"] for n in node_statuses if n["fragility_score"] >= t)
    node_count = max(1, int(fragility.get("node_count", len(node_statuses))))
    breach_count = len(breached)
    return {
        "failure_threshold": t,
        "threshold_breaches": breached,
        "threshold_breach_count": breach_count,
        "system_threshold_breached": _bound01(float(fragility.get("system_fragility_score", 0.0))) >= t,
        "threshold_breach_ratio": _bound01(breach_count / node_count),
        "node_threshold_statuses": node_statuses,
    }
