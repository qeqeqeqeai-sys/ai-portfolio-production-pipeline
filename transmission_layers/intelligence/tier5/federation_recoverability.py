from __future__ import annotations

from .federation_common import clamp_score, mean_bounded
from .federation_resilience_signatures import federation_resilience_checksum


def federation_recoverability_assessment(recovery: dict[str, float], temporal: dict[str, float], health: dict[str, float]) -> dict[str, float | str]:
    recoverability = mean_bounded([
        recovery.get("federation_recovery_readiness_score", 0.0),
        1.0 - temporal.get("federation_evolution_score", 0.0),
        health.get("federation_structural_health_score", 0.0),
    ])
    classification = "recoverable" if recoverability >= 0.66 else "structurally_brittle" if recoverability < 0.33 else "replay_recovery_limited"
    result = {
        "federation_recoverability_score": clamp_score(recoverability),
        "federation_resilience_classification": classification,
    }
    result["federation_recoverability_checksum"] = federation_resilience_checksum(result, "tier5g_recoverability")
    return result
