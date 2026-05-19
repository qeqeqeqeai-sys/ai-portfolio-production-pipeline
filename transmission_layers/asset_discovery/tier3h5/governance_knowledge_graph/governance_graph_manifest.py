from __future__ import annotations

from hashlib import sha256
from typing import Any


def build_graph_manifest(context: dict[str, Any], node_inventory: dict[str, Any], edge_inventory: dict[str, Any]) -> dict[str, Any]:
    seed = "|".join(sorted(context["loaded_inputs"].keys()))
    manifest_id = f"gkg_{sha256(seed.encode()).hexdigest()[:16]}"
    return {
        "governance_graph_manifest_id": manifest_id,
        "phases_covered": sorted(context["phase_coverage"].keys()),
        "phase_coverage": context["phase_coverage"],
        "loaded_input_count": context["loaded_input_count"],
        "missing_input_count": context["missing_input_count"],
        "graph_nodes_generated": node_inventory["graph_nodes_generated"],
        "graph_edges_generated": edge_inventory["graph_edges_generated"],
        "governance_graph_replayable": True,
        "exact_match_only_preserved": True,
    }
