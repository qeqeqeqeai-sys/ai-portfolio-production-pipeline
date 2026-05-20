from __future__ import annotations


def explain_regime_transition(payload: dict[str, object]) -> str:
    return (
        "transition intelligence template: "
        f"transition_id={payload.get('transition_id','')} "
        f"transition_classification={payload.get('transition_classification','')} "
        f"dominant_transition_factor={payload.get('dominant_transition_factor','')} "
        f"transition_vulnerability_score={float(payload.get('transition_vulnerability_score',0.0)):.6f} "
        f"transition_checksum={payload.get('transition_checksum','')}"
    )
