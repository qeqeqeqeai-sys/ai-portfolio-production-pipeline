from __future__ import annotations

from typing import Any


def build_invariant_dependency_surface(edge_inventory: dict[str, Any]) -> dict[str, Any]:
    mapping: dict[str, list[str]] = {}
    for edge in edge_inventory["edges"]:
        if edge["edge_type"] in {"verifies_invariant", "depends_on_invariant"}:
            mapping.setdefault(edge["to_node_id"], []).append(edge["from_node_id"])
    for key in mapping:
        mapping[key] = sorted(mapping[key])
    return {
        "invariant_dependencies": dict(sorted(mapping.items())),
        "invariants_mapped": len(mapping),
        "advisory_only_governance_verified": True,
    }
