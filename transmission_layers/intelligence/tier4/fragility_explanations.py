from __future__ import annotations

from typing import Any


def explain_fragility(summary: dict[str, Any]) -> str:
    return (
        "fragility status template: "
        f"fragility_id={str(summary.get('fragility_id', 'tier4_fragility'))}; "
        f"fragility_score={round(float(summary.get('fragility_score', summary.get('system_fragility_score', 0.0))), 6)}; "
        f"bounded_fragility_score={round(float(summary.get('bounded_fragility_score', summary.get('system_fragility_score', 0.0))), 6)}; "
        f"dominant_fragility_factor={str(summary.get('dominant_fragility_factor', 'overload'))}; "
        f"fragility_classification={str(summary.get('fragility_classification', 'stable'))}; "
        f"structural_survivability_score={round(float(summary.get('structural_survivability_score', 0.0)), 6)}; "
        f"threshold_proximity_score={round(float(summary.get('threshold_proximity_score', 0.0)), 6)}; "
        f"fragility_checksum={str(summary.get('fragility_checksum', ''))}."
    )
