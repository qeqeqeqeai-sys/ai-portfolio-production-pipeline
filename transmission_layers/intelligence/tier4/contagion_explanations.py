from __future__ import annotations


def explain_contagion(payload: dict[str, object]) -> str:
    return (
        "contagion intelligence template: "
        f"contagion_id={payload.get('contagion_id','')} "
        f"contagion_classification={payload.get('contagion_classification','')} "
        f"dominant_contagion_factor={payload.get('dominant_contagion_factor','')} "
        f"stress_concentration_score={float(payload.get('stress_concentration_score',0.0)):.6f} "
        f"stress_amplification_score={float(payload.get('stress_amplification_score',0.0)):.6f} "
        f"contagion_checksum={payload.get('contagion_checksum','')}"
    )
