from __future__ import annotations


def federation_health_classification(health_score: float, degradation: float, readiness: dict[str, float]) -> str:
    if health_score >= 0.8 and degradation <= 0.2:
        return "healthy"
    if readiness["observability_alignment_score"] >= 0.7 and degradation >= 0.5:
        return "observable_but_degraded"
    if readiness["diagnostic_readiness_score"] < 0.4:
        return "diagnostically_limited"
    if readiness["governance_alignment_score"] < 0.4:
        return "governance_constrained"
    if readiness["replay_health_score"] < 0.4:
        return "replay_insufficient"
    if readiness["continuity_health_score"] < 0.4:
        return "continuity_fragile"
    if readiness["propagation_health_score"] < 0.4:
        return "propagation_degraded"
    return "structurally_degraded"
