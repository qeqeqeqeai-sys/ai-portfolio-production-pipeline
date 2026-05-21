from __future__ import annotations

from .federation_common import clamp_score, mean_bounded


def federation_degradation_score(readiness: dict[str, float]) -> dict[str, float]:
    base = mean_bounded([
        1.0 - readiness["observability_alignment_score"],
        1.0 - readiness["governance_alignment_score"],
        1.0 - readiness["replay_health_score"],
        1.0 - readiness["continuity_health_score"],
        1.0 - readiness["propagation_health_score"],
    ])
    return {"health_degradation_score": clamp_score(base)}
