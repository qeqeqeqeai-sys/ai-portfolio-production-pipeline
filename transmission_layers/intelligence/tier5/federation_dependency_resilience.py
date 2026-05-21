from __future__ import annotations

from typing import Any

from .federation_common import clamp_score, mean_bounded
from .federation_resilience_signatures import federation_resilience_checksum


def federation_dependency_resilience(dependencies: list[dict[str, Any]], governance: dict[str, Any]) -> dict[str, float]:
    dep_sorted = sorted((str(d.get("source", "")), str(d.get("target", ""))) for d in dependencies)
    nodes = sorted({n for pair in dep_sorted for n in pair if n})
    single_points = 0
    for node in nodes:
        inbound = sum(1 for _, t in dep_sorted if t == node)
        outbound = sum(1 for s, _ in dep_sorted if s == node)
        if inbound + outbound <= 1:
            single_points += 1
    fragility = 1.0 if not nodes else single_points / len(nodes)
    score = clamp_score(1.0 - fragility)
    result = {
        "federation_dependency_resilience_score": mean_bounded([score, governance.get("federation_guardrails_score", 0.0)]),
    }
    result["federation_dependency_resilience_checksum"] = federation_resilience_checksum(result, "tier5g_dependency")
    return result
