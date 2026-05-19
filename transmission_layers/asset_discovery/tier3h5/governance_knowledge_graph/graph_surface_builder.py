from __future__ import annotations

from hashlib import sha256
from typing import Any

ALLOWED_EDGE_TYPES = {
    "produced_by_phase",
    "consumed_by_phase",
    "derived_from_artifact",
    "summarizes_artifact",
    "verifies_invariant",
    "depends_on_invariant",
    "continues_state",
    "reports_posture",
    "traces_lineage",
    "covers_phase",
}


def _node_id(kind: str, value: str) -> str:
    return f"node_{sha256(f'{kind}:{value}'.encode()).hexdigest()[:16]}"


def _edge_id(src: str, edge_type: str, dst: str) -> str:
    return f"edge_{sha256(f'{src}:{edge_type}:{dst}'.encode()).hexdigest()[:16]}"


def build_graph_surfaces(context: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    for phase in sorted(context["phase_inputs"]):
        phase_node = _node_id("phase", phase)
        nodes[phase_node] = {"node_id": phase_node, "node_type": "phase", "node_key": phase}
        for artifact in sorted(context["phase_inputs"][phase]):
            artifact_node = _node_id("artifact", artifact)
            nodes[artifact_node] = {
                "node_id": artifact_node,
                "node_type": "artifact",
                "node_key": artifact,
                "present": context["artifact_coverage"].get(artifact, False),
            }
            edges.append(
                {
                    "edge_id": _edge_id(artifact_node, "produced_by_phase", phase_node),
                    "edge_type": "produced_by_phase",
                    "from_node_id": artifact_node,
                    "to_node_id": phase_node,
                }
            )

    inv_path = "logs/tier3h5_governance_invariant_registry.json"
    inv = context["loaded_inputs"].get(inv_path, {}) if isinstance(context["loaded_inputs"].get(inv_path, {}), dict) else {}
    for invariant_key in sorted(inv):
        invariant_node = _node_id("invariant", invariant_key)
        nodes[invariant_node] = {"node_id": invariant_node, "node_type": "invariant", "node_key": invariant_key}
        for artifact in sorted(context["loaded_inputs"]):
            if "summary" in artifact or "registry" in artifact:
                artifact_node = _node_id("artifact", artifact)
                edge_type = "verifies_invariant" if "summary" in artifact else "depends_on_invariant"
                edges.append(
                    {
                        "edge_id": _edge_id(artifact_node, edge_type, invariant_node),
                        "edge_type": edge_type,
                        "from_node_id": artifact_node,
                        "to_node_id": invariant_node,
                    }
                )

    edges = sorted(edges, key=lambda e: (e["edge_type"], e["from_node_id"], e["to_node_id"]))
    assert all(edge["edge_type"] in ALLOWED_EDGE_TYPES for edge in edges)
    return (
        {"nodes": [nodes[k] for k in sorted(nodes)], "graph_nodes_generated": len(nodes)},
        {"edges": edges, "graph_edges_generated": len(edges), "allowed_edge_types": sorted(ALLOWED_EDGE_TYPES)},
    )
