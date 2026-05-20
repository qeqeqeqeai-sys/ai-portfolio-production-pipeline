from __future__ import annotations

from .federation_common import clamp_score


def federation_escalation_diagnostics(violation_score: float, recurrence_score: float) -> dict[str, float | str]:
    escalation = clamp_score((violation_score * 0.7) + (recurrence_score * 0.3))
    if escalation >= 0.66:
        cls = "deterministic_escalation_required"
    elif escalation >= 0.33:
        cls = "deterministic_watch"
    else:
        cls = "deterministic_stable"
    return {"federation_escalation_score": escalation, "federation_governance_classification": cls}
