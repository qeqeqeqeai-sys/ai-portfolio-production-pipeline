from __future__ import annotations

from typing import Any

from .federation_common import clamp_score, mean_bounded, weighted_bounded_score


def federation_diagnostic_readiness(governance: dict[str, Any], observability: dict[str, Any], persistence: dict[str, Any]) -> dict[str, float]:
    observability_alignment_score = clamp_score(observability.get("federation_observability_score", 0.0))
    governance_alignment_score = clamp_score(1.0 - governance.get("federation_violation_score", governance.get("federation_governance_score", 0.0)))
    replay_health_score = clamp_score(persistence.get("federation_replay_consistency_score", persistence.get("federation_persistence_score", 0.0)))
    continuity_health_score = clamp_score(mean_bounded([
        observability.get("federation_continuity_observability_score", 0.0),
        governance.get("federation_continuity_constraint_score", 0.0),
    ]))
    propagation_health_score = clamp_score(mean_bounded([
        observability.get("federation_propagation_visibility_score", 0.0),
        governance.get("governance_containment_effectiveness_score", 0.0),
    ]))
    diagnostic_readiness_score = weighted_bounded_score([
        (observability_alignment_score, 0.25),
        (governance_alignment_score, 0.2),
        (replay_health_score, 0.2),
        (continuity_health_score, 0.2),
        (propagation_health_score, 0.15),
    ])
    return {
        "diagnostic_readiness_score": diagnostic_readiness_score,
        "observability_alignment_score": observability_alignment_score,
        "governance_alignment_score": governance_alignment_score,
        "replay_health_score": replay_health_score,
        "continuity_health_score": continuity_health_score,
        "propagation_health_score": propagation_health_score,
    }
