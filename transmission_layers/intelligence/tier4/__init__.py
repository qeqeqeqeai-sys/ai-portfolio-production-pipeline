"""Tier 4 deterministic structural simulation and memory package."""

__all__ = [
    "run_structural_simulation",
    "StructuralMemoryStore",
    "compare_snapshots",
    "replay_structural_timeline",
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
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
