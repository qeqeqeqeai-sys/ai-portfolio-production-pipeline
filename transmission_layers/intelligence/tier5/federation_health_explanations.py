from __future__ import annotations


def fixed_federation_health_explanations(result: dict[str, object]) -> dict[str, str]:
    return {
        "federation_health_explanation_headline": "Tier 5F federation structural health computed deterministically with bounded diagnostics.",
        "federation_health_explanation_detail": (
            "classification={classification}; structural={structural:.4f}; readiness={readiness:.4f}; degradation={degradation:.4f}; dominant={dominant}"
        ).format(
            classification=result["federation_health_classification"],
            structural=float(result["federation_structural_health_score"]),
            readiness=float(result["diagnostic_readiness_score"]),
            degradation=float(result["health_degradation_score"]),
            dominant=result["dominant_health_factor"],
        ),
    }
