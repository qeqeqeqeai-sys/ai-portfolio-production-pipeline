from __future__ import annotations


def explain_structural_rigidity(summary: dict[str, object]) -> str:
    return (
        "deterministic rigidity diagnostics: "
        f"classification={summary.get('rigidity_classification', 'unknown')}; "
        f"dominant_factor={summary.get('dominant_rigidity_factor', 'none')}; "
        f"rigidity={round(float(summary.get('structural_rigidity_score', 0.0)), 6)}; "
        f"constraints={round(float(summary.get('adaptation_constraint_score', 0.0)), 6)}; "
        f"saturation={round(float(summary.get('resilience_saturation_score', 0.0)), 6)}."
    )[:280]
