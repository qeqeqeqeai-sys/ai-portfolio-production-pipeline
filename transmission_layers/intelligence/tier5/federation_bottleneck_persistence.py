from __future__ import annotations


def bottleneck_persistence_score(bottleneck_history: list[list[str]]) -> float:
    if not bottleneck_history:
        return 0.0
    counts: dict[str, int] = {}
    for bottlenecks in bottleneck_history:
        for item in sorted(bottlenecks):
            counts[item] = counts.get(item, 0) + 1
    if not counts:
        return 0.0
    n = len(bottleneck_history)
    return max(0.0, min(1.0, sum(v / n for _, v in sorted(counts.items())) / len(counts)))
