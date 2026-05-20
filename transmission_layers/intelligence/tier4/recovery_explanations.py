from __future__ import annotations


def explain_structural_recovery(summary: dict[str, object]) -> str:
    return (
        "deterministic recovery diagnostics: "
        f"classification={summary.get('recovery_classification', 'unknown')}; "
        f"dominant_factor={summary.get('dominant_recovery_factor', 'none')}; "
        f"recovery={round(float(summary.get('structural_recovery_score', 0.0)), 6)}; "
        f"reintegration={round(float(summary.get('reintegration_stability_score', 0.0)), 6)}; "
        f"relapse={round(float(summary.get('recovery_relapse_score', 0.0)), 6)}."
    )[:280]
