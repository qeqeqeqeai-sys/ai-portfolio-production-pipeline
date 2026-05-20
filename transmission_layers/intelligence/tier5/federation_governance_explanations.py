from __future__ import annotations


def fixed_federation_governance_explanations(result: dict[str, object]) -> dict[str, str]:
    return {
        "federation_governance_explanation": (
            "Deterministic governance diagnostics combine constraint pressure, guardrail breaches, "
            "boundary enforcement, continuity stability, and recurrence to classify governance state."
        ),
        "federation_governance_dominant_factor_explanation": (
            f"Dominant governance factor is {result.get('dominant_governance_factor', 'none')} based on sorted bounded scores."
        ),
    }
