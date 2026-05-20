from __future__ import annotations

from .federation_common import clamp_score


def federation_violation_score(*, constraint_score: float, guardrail_score: float, boundary_enforcement_score: float, continuity_score: float) -> dict[str, float]:
    violation = clamp_score((constraint_score + guardrail_score + (1.0 - boundary_enforcement_score) + (1.0 - continuity_score)) / 4.0)
    return {"federation_violation_score": violation}
