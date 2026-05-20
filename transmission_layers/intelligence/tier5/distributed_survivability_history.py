from __future__ import annotations


def survivability_dependency_recurrence_score(history: list[list[tuple[str, str]]]) -> float:
    if not history:
        return 0.0
    counts: dict[tuple[str, str], int] = {}
    for dependencies in history:
        for dep in sorted(dependencies):
            counts[dep] = counts.get(dep, 0) + 1
    if not counts:
        return 0.0
    n = len(history)
    return max(0.0, min(1.0, sum(v / n for _, v in sorted(counts.items())) / len(counts)))
