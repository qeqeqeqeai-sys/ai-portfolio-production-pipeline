from __future__ import annotations

from typing import Any, Dict

TEMPLATES = {
    "reinforce_resilience": "resilience reinforcement reduced overload concentration around dominant chokepoints.",
    "isolate_corridors": "corridor isolation reduced fragmentation propagation.",
    "suppress_cascade_paths": "suppression response stabilized contagion amplification pathways.",
    "limited_recovery": "response intervention produced limited structural recovery.",
}


def explain_response_policy(response_type: str, factors: Dict[str, Any] | None = None) -> str:
    base = TEMPLATES.get(response_type, TEMPLATES["limited_recovery"])
    if not factors:
        return base
    ordered = sorted((str(k), float(v)) for k, v in factors.items())[:3]
    suffix = "; ".join(f"{k}={round(v, 6)}" for k, v in ordered)
    out = f"{base} factors: {suffix}."
    return out[:280]
