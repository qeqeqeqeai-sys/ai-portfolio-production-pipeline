from __future__ import annotations

from typing import Any

from .federation_common import clamp_score, mean_bounded
from .federation_resilience_signatures import federation_resilience_checksum


def federation_failure_containment(contagion_paths: list[dict[str, Any]], governance: dict[str, Any], observability: dict[str, Any]) -> dict[str, float]:
    ordered = sorted(contagion_paths, key=lambda p: (str(p.get("path_id", "")), str(p.get("source", "")), str(p.get("target", ""))))
    if not ordered:
        contained_ratio = 0.0
    else:
        contained_ratio = sum(1.0 for p in ordered if bool(p.get("contained", False))) / len(ordered)
    score = mean_bounded([contained_ratio, governance.get("federation_violation_detection_score", 0.0), observability.get("federation_propagation_visibility_score", 0.0)])
    result = {"federation_failure_containment_score": clamp_score(score)}
    result["federation_failure_containment_checksum"] = federation_resilience_checksum(result, "tier5g_containment")
    return result
