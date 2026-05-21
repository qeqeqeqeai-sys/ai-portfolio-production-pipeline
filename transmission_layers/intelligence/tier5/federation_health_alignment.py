from __future__ import annotations

from .federation_common import clamp_score


def federation_health_alignment(readiness: dict[str, float]) -> dict[str, float]:
    scores = [
        readiness["observability_alignment_score"],
        readiness["governance_alignment_score"],
        readiness["replay_health_score"],
        readiness["continuity_health_score"],
        readiness["propagation_health_score"],
    ]
    spread = max(scores) - min(scores) if scores else 0.0
    return {"federation_health_alignment_score": clamp_score(1.0 - spread)}
