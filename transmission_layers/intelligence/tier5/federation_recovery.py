from __future__ import annotations

from typing import Any

from .federation_common import clamp_score, mean_bounded
from .federation_resilience_signatures import federation_resilience_checksum


def federation_recovery_readiness(governance: dict[str, Any], persistence: dict[str, Any], observability: dict[str, Any]) -> dict[str, Any]:
    score = mean_bounded([
        governance.get("federation_governance_score", 0.0),
        governance.get("continuity_constraints_score", 0.0),
        persistence.get("federation_persistence_score", 0.0),
        persistence.get("federation_recovery_history_score", 0.0),
        observability.get("federation_observability_score", 0.0),
        observability.get("federation_continuity_observability_score", 0.0),
        observability.get("federation_replay_observability_score", 0.0),
    ])
    result = {
        "federation_recovery_readiness_score": score,
        "federation_irreversibility_risk_score": clamp_score(1.0 - mean_bounded([
            persistence.get("federation_replay_history_score", 0.0),
            persistence.get("federation_recovery_history_score", 0.0),
            governance.get("policy_boundaries_score", 0.0),
        ])),
        "federation_recovery_gap_score": clamp_score(1.0 - score),
    }
    result["federation_recovery_checksum"] = federation_resilience_checksum(result, "tier5g_recovery")
    return result
