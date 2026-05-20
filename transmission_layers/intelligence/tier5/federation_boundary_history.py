from __future__ import annotations


def boundary_recurrence_score(boundary_history: list[list[str]]) -> float:
    if not boundary_history:
        return 0.0
    counts: dict[str, int] = {}
    for boundaries in boundary_history:
        for item in sorted(boundaries):
            counts[item] = counts.get(item, 0) + 1
    if not counts:
        return 0.0
    n = len(boundary_history)
    return max(0.0, min(1.0, sum(v / n for _, v in sorted(counts.items())) / len(counts)))
