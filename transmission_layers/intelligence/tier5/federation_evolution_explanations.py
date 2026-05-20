from __future__ import annotations


def fixed_federation_evolution_explanations(result: dict[str, object]) -> dict[str, str]:
    return {
        "federation_evolution_explanation_headline": "Tier 5C federation temporal evolution diagnostics computed deterministically.",
        "federation_evolution_explanation_detail": (
            "topology={:.4f}; phase={:.4f}; bridge={:.4f}; dependency={:.4f}; boundary={:.4f}; "
            "contagion={:.4f}; bottleneck={:.4f}; survivability={:.4f}; recovery={:.4f}; continuity={:.4f}"
        ).format(
            float(result.get("topology_evolution_score", 0.0)),
            float(result.get("phase_transition_score", 0.0)),
            float(result.get("bridge_evolution_score", 0.0)),
            float(result.get("dependency_evolution_score", 0.0)),
            float(result.get("boundary_evolution_score", 0.0)),
            float(result.get("contagion_evolution_score", 0.0)),
            float(result.get("bottleneck_evolution_score", 0.0)),
            float(result.get("survivability_evolution_score", 0.0)),
            float(result.get("recovery_evolution_score", 0.0)),
            float(result.get("continuity_evolution_score", 0.0)),
        ),
    }
