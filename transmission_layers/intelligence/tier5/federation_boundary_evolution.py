from __future__ import annotations

from .federation_common import clamp_score


def federation_boundary_evolution_score(history: list[list[str]]) -> float:
    if len(history) <= 1:
        return 0.0
    shifts = []
    for i in range(1, len(history)):
        prev = set(history[i - 1])
        curr = set(history[i])
        shifts.append(len(prev ^ curr) / max(1, len(prev | curr)))
    return clamp_score(sum(shifts) / len(shifts))
