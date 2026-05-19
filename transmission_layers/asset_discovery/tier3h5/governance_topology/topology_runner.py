from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .continuity_chain_builder import build_continuity_chains
from .coverage_topology import build_coverage_topology
from .dependency_graph_builder import build_dependency_graph
from .governance_topology_manifest import build_topology_manifest
from .invariant_topology import build_invariant_topology
from .state_transition_topology import build_state_transition_topology
from .topology_context import load_topology_context, stable_json_dumps
from .topology_summary import build_topology_summary


def _write(path: str, payload: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(stable_json_dumps(payload), encoding="utf-8")


def run_governance_topology() -> dict[str, Any]:
    context = load_topology_context()
    manifest = build_topology_manifest(context)
    graph = build_dependency_graph(context)
    chains = build_continuity_chains()
    invariants = build_invariant_topology()
    transitions = build_state_transition_topology(manifest)
    coverage = build_coverage_topology(context)
    summary = build_topology_summary(
        manifest=manifest,
        graph=graph,
        chains=chains,
        invariants=invariants,
        transitions=transitions,
        coverage=coverage,
        context=context,
    )

    _write("logs/tier3h5_topology_context.json", context)
    _write("logs/tier3h5_governance_topology_manifest.json", manifest)
    _write("logs/tier3h5_governance_dependency_graph.json", graph)
    _write("logs/tier3h5_continuity_chain_summary.json", chains)
    _write("logs/tier3h5_invariant_topology_summary.json", invariants)
    _write("logs/tier3h5_state_transition_topology.json", transitions)
    _write("logs/tier3h5_coverage_topology_summary.json", coverage)
    _write("logs/tier3h5_phase5g_topology_summary.json", summary)

    history_root = Path("logs/history/tier3h5_governance_topology")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    history_dir = history_root / run_id
    _write(str(history_dir / "governance_topology_manifest.json"), manifest)
    _write(str(history_dir / "governance_dependency_graph.json"), graph)
    _write(str(history_dir / "continuity_chain_summary.json"), chains)
    _write(str(history_dir / "invariant_topology_summary.json"), invariants)
    _write(str(history_dir / "state_transition_topology.json"), transitions)
    _write(str(history_dir / "coverage_topology_summary.json"), coverage)
    _write(str(history_dir / "topology_summary.json"), summary)
    return summary
