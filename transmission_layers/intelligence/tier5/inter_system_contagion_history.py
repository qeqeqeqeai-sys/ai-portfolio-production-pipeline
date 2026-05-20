from __future__ import annotations


def contagion_corridor_persistence_score(corridor_history: list[list[tuple[str, str]]]) -> float:
    if not corridor_history:
        return 0.0
    counts: dict[tuple[str, str], int] = {}
    for corridors in corridor_history:
        for corridor in sorted(corridors):
            counts[corridor] = counts.get(corridor, 0) + 1
    if not counts:
        return 0.0
    n = len(corridor_history)
    return max(0.0, min(1.0, sum(v / n for _, v in sorted(counts.items())) / len(counts)))
