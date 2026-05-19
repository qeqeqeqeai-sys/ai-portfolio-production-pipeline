from __future__ import annotations

from typing import Any


def build_traversal_surfaces(context: dict[str, Any], node_inventory: dict[str, Any], edge_inventory: dict[str, Any], max_depth: int = 2) -> dict[str, Any]:
    phase_to_artifacts = {
        phase: sorted(paths)
        for phase, paths in sorted(context["phase_inputs"].items())
    }
    artifact_to_phase = {
        artifact: phase
        for phase, artifacts in phase_to_artifacts.items()
        for artifact in artifacts
    }
    traversal_paths_generated = len(artifact_to_phase) + len(phase_to_artifacts)
    return {
        "max_depth": max_depth,
        "exact_match_only": True,
        "artifact_to_phase_path": artifact_to_phase,
        "phase_to_produced_artifacts": phase_to_artifacts,
        "invariant_to_verifying_artifacts": {
            edge["to_node_id"]: [] for edge in edge_inventory["edges"] if edge["edge_type"] == "verifies_invariant"
        },
        "topology_to_dependency_edges": [
            edge for edge in edge_inventory["edges"] if edge["edge_type"] in {"produced_by_phase", "depends_on_invariant"}
        ],
        "traversal_paths_generated": traversal_paths_generated,
    }
