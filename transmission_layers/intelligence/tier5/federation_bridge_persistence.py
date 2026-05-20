from __future__ import annotations


def bridge_persistence_score(bridge_history: list[list[tuple[str, str]]]) -> float:
    if not bridge_history:
        return 0.0
    if len(bridge_history) == 1:
        return 1.0 if bridge_history[0] else 0.0
    counts: dict[tuple[str, str], int] = {}
    for bridges in bridge_history:
        for bridge in sorted(bridges):
            counts[bridge] = counts.get(bridge, 0) + 1
    if not counts:
        return 0.0
    denom = len(bridge_history)
    return max(0.0, min(1.0, sum(v / denom for _, v in sorted(counts.items())) / len(counts)))
