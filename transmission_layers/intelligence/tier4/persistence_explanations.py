from __future__ import annotations

from typing import Any


def explain_persistence_durability(payload: dict[str, Any]) -> str:
    return (
        "persistence durability template: "
        f"durability_id={payload.get('durability_id','')} "
        f"durability_score={float(payload.get('durability_score',0.0)):.6f} "
        f"resilience_erosion_score={float(payload.get('resilience_erosion_score',0.0)):.6f} "
        f"stabilization_longevity_score={float(payload.get('stabilization_longevity_score',0.0)):.6f} "
        f"chronic_instability_score={float(payload.get('chronic_instability_score',0.0)):.6f} "
        f"durability_classification={payload.get('durability_classification','')} "
        f"persistence_checksum={payload.get('persistence_checksum','')}"
    )
