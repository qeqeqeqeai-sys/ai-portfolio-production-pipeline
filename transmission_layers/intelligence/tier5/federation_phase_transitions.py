from __future__ import annotations

from .federation_common import clamp_score


def federation_phase_transition_score(topology_counts: list[int]) -> float:
    if len(topology_counts) <= 1:
        return 0.0
    transitions = sum(1 for i in range(1, len(topology_counts)) if topology_counts[i] != topology_counts[i - 1])
    return clamp_score(transitions / (len(topology_counts) - 1))
