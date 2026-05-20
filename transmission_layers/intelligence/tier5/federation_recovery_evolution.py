from __future__ import annotations

from .federation_common import clamp_score


def federation_recovery_evolution_score(history: list[list[tuple[str, str]]]) -> float:
    if len(history) <= 1:
        return 0.0
    ratios = []
    for i in range(1, len(history)):
        prev = set(history[i - 1])
        curr = set(history[i])
        ratios.append(len(prev ^ curr) / max(1, len(prev | curr)))
    return clamp_score(sum(ratios) / len(ratios))
