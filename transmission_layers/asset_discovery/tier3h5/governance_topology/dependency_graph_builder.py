from __future__ import annotations

from typing import Any

PHASE_ORDER = ("phase5a", "phase5b", "phase5c", "phase5d", "phase5e", "phase5f", "phase5g")


def build_dependency_graph(context: dict[str, Any]) -> dict[str, Any]:
    nodes = [{"node_id": phase, "covered": context["phase_coverage"].get(phase, phase == "phase5g")} for phase in PHASE_ORDER]
    edges: list[dict[str, str]] = []
    for idx in range(len(PHASE_ORDER) - 1):
        source, target = PHASE_ORDER[idx], PHASE_ORDER[idx + 1]
        if source != "phase5g":
            edges.append({"source": source, "target": target, "relationship": "deterministic_dependency"})
    return {
        "dependency_graph_status": "generated",
        "graph_nodes": sorted(nodes, key=lambda x: x["node_id"]),
        "graph_edges": sorted(edges, key=lambda x: (x["source"], x["target"])),
        "topology_nodes_generated": len(nodes),
        "topology_edges_generated": len(edges),
    }
