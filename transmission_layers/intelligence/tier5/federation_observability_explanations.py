from __future__ import annotations


def fixed_federation_observability_explanations(result: dict[str, object]) -> dict[str, str]:
    return {
        "federation_observability_explanation": "Deterministic distributed observability combines visibility, lineage, traceability, telemetry, propagation visibility, continuity, and replay metrics.",
        "federation_observability_dominant_factor_explanation": f"Dominant observability factor is {result.get('dominant_observability_factor', 'none')} using deterministic sorted tie-break ordering.",
    }
