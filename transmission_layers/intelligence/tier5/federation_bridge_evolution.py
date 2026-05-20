from __future__ import annotations

from .federation_common import clamp_score


def federation_bridge_evolution_score(bridge_history: list[list[tuple[str, str]]]) -> float:
    if len(bridge_history) <= 1:
        return 0.0
    deltas = []
    for i in range(1, len(bridge_history)):
        prev = set(bridge_history[i - 1])
        curr = set(bridge_history[i])
        denom = max(1, len(prev | curr))
        deltas.append(len(prev ^ curr) / denom)
    return clamp_score(sum(deltas) / len(deltas))
