from __future__ import annotations


def fixed_federation_persistence_explanations(metrics: dict[str, float | str | int]) -> dict[str, str]:
    headline = "Tier 5B federation persistence computed deterministically from replay history."
    detail_keys = [
        "federation_persistence_score",
        "bridge_persistence_score",
        "boundary_recurrence_score",
        "contagion_corridor_persistence_score",
        "bottleneck_persistence_score",
        "survivability_dependency_recurrence_score",
        "recovery_dependency_recurrence_score",
        "federation_signature_stability_score",
        "federation_continuity_drift_score",
    ]
    detail = "; ".join(f"{k}={float(metrics.get(k, 0.0)):.4f}" for k in detail_keys)
    return {
        "federation_persistence_explanation_headline": headline,
        "federation_persistence_explanation_detail": detail,
    }
