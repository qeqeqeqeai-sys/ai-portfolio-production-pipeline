from __future__ import annotations

from typing import Any


def explain_fragility(summary: dict[str, Any]) -> str:
    score = round(float(summary.get("system_fragility_score", 0.0)), 6)
    breaches = int(summary.get("threshold_breach_count", 0))
    irreversible = bool(summary.get("cascade_irreversibility_detected", False))
    band = "low" if score < 0.34 else "moderate" if score < 0.67 else "high"
    irreversible_txt = "yes" if irreversible else "no"
    return (
        "fragility status template: "
        f"band={band}; system_fragility_score={score}; threshold_breach_count={breaches}; "
        f"cascade_irreversibility_detected={irreversible_txt}."
    )
