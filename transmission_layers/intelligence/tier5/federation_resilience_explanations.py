from __future__ import annotations


def fixed_federation_resilience_explanations(result: dict[str, object]) -> dict[str, str]:
    return {
        "federation_resilience_explanation_headline": "Tier 5G federation resilience and recovery state computed deterministically with bounded diagnostics.",
        "federation_resilience_explanation_detail": (
            "classification={classification}; resilience={resilience:.4f}; recovery={recovery:.4f}; recoverability={recoverability:.4f}; dependency={dependency:.4f}; containment={containment:.4f}; paths={paths:.4f}; irreversibility={irreversibility:.4f}; gap={gap:.4f}; dominant={dominant}"
        ).format(
            classification=result["federation_resilience_classification"],
            resilience=float(result["federation_resilience_score"]),
            recovery=float(result["federation_recovery_readiness_score"]),
            recoverability=float(result["federation_recoverability_score"]),
            dependency=float(result["federation_dependency_resilience_score"]),
            containment=float(result["federation_failure_containment_score"]),
            paths=float(result["federation_recovery_path_score"]),
            irreversibility=float(result["federation_irreversibility_risk_score"]),
            gap=float(result["federation_recovery_gap_score"]),
            dominant=result["dominant_resilience_factor"],
        ),
    }
