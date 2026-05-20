from __future__ import annotations

from typing import Any

from .federation_common import clamp_score


def federation_guardrail_diagnostics(contagion_paths: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(contagion_paths, key=lambda x: (str(x.get("source", "")), str(x.get("target", "")), str(x.get("path_id", ""))))
    if not ordered:
        return {"federation_guardrail_score": 0.0, "governance_containment_effectiveness_score": 1.0}
    breach_count = sum(1 for p in ordered if float(p.get("stress", 0.0)) >= float(p.get("guardrail_limit", 1.0)))
    containment_hits = sum(1 for p in ordered if bool(p.get("contained", False)))
    guardrail = clamp_score(breach_count / len(ordered))
    containment = clamp_score(containment_hits / len(ordered))
    return {
        "federation_guardrail_score": guardrail,
        "governance_containment_effectiveness_score": containment,
    }
