from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .coverage_graph_export import build_coverage_graph_export
from .governance_graph_manifest import build_graph_manifest
from .governance_graph_summary import build_knowledge_graph_summary
from .graph_surface_builder import build_graph_surfaces
from .invariant_dependency_surface import build_invariant_dependency_surface
from .knowledge_graph_context import load_knowledge_graph_context, stable_json_dumps
from .reachability_surface import build_reachability_summary
from .traversal_surface_builder import build_traversal_surfaces


def _write(path: str, payload: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(stable_json_dumps(payload), encoding="utf-8")


def run_governance_knowledge_graph() -> dict[str, Any]:
    context = load_knowledge_graph_context()
    nodes, edges = build_graph_surfaces(context)
    manifest = build_graph_manifest(context, nodes, edges)
    traversals = build_traversal_surfaces(context, nodes, edges)
    invariant_surface = build_invariant_dependency_surface(edges)
    reachability = build_reachability_summary(context)
    coverage = build_coverage_graph_export(context)
    summary = build_knowledge_graph_summary(manifest, nodes, edges, traversals, invariant_surface, reachability, coverage)

    _write("logs/tier3h5_knowledge_graph_context.json", context)
    _write("logs/tier3h5_governance_knowledge_graph_manifest.json", manifest)
    _write("logs/tier3h5_governance_graph_node_inventory.json", nodes)
    _write("logs/tier3h5_governance_graph_edge_inventory.json", edges)
    _write("logs/tier3h5_governance_traversal_surfaces.json", traversals)
    _write("logs/tier3h5_invariant_dependency_surface.json", invariant_surface)
    _write("logs/tier3h5_governance_reachability_summary.json", reachability)
    _write("logs/tier3h5_governance_coverage_graph_export.json", coverage)
    _write("logs/tier3h5_phase5h_knowledge_graph_summary.json", summary)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    history_dir = Path("logs/history/tier3h5_knowledge_graph") / run_id
    _write(str(history_dir / "governance_knowledge_graph_manifest.json"), manifest)
    _write(str(history_dir / "governance_graph_node_inventory.json"), nodes)
    _write(str(history_dir / "governance_graph_edge_inventory.json"), edges)
    _write(str(history_dir / "governance_traversal_surfaces.json"), traversals)
    _write(str(history_dir / "knowledge_graph_summary.json"), summary)
    return summary
