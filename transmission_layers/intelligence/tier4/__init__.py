"""Tier 4 deterministic structural simulation and memory package."""

__all__ = [
    "run_structural_simulation",
    "StructuralMemoryStore",
    "compare_snapshots",
    "replay_structural_timeline",
    "compute_structural_influence_summary",
    "trace_causal_lineage",
    "replay_causal_influence",
]


def __getattr__(name: str):
    if name == "run_structural_simulation":
        from .structural_simulation import run_structural_simulation

        return run_structural_simulation
    if name == "StructuralMemoryStore":
        from .structural_memory import StructuralMemoryStore

        return StructuralMemoryStore
    if name in {"compare_snapshots", "replay_structural_timeline"}:
        from .temporal_replay import compare_snapshots, replay_structural_timeline

        return compare_snapshots if name == "compare_snapshots" else replay_structural_timeline
    tier4c = _tier4c_getattr(name)
    if tier4c is not None:
        return tier4c
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def _tier4c_getattr(name: str):
    if name == "compute_structural_influence_summary":
        from .influence_attribution import compute_structural_influence_summary

        return compute_structural_influence_summary
    if name == "trace_causal_lineage":
        from .causal_lineage import trace_causal_lineage

        return trace_causal_lineage
    if name == "replay_causal_influence":
        from .causal_replay import replay_causal_influence

        return replay_causal_influence
    return None
