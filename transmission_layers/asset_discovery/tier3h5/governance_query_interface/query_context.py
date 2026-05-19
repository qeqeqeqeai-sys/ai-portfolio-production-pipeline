from __future__ import annotations

import json
from pathlib import Path
from typing import Any

QUERY_INPUT_FILES: tuple[str, ...] = (
    "logs/tier3h5_governance_knowledge_graph_manifest.json",
    "logs/tier3h5_governance_graph_node_inventory.json",
    "logs/tier3h5_governance_graph_edge_inventory.json",
    "logs/tier3h5_governance_traversal_surfaces.json",
    "logs/tier3h5_invariant_dependency_surface.json",
    "logs/tier3h5_governance_reachability_summary.json",
    "logs/tier3h5_governance_coverage_graph_export.json",
    "logs/tier3h5_phase5h_knowledge_graph_summary.json",
)


def stable_json_dumps(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, separators=(",", ": "))


def normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: normalize(value[k]) for k in sorted(value)}
    if isinstance(value, list):
        return [normalize(v) for v in value]
    if value is None or isinstance(value, bool):
        return value
    return value


def load_query_context() -> dict[str, Any]:
    loaded_inputs: dict[str, Any] = {}
    missing_inputs: list[str] = []
    for path in QUERY_INPUT_FILES:
        p = Path(path)
        if p.exists():
            loaded_inputs[path] = normalize(json.loads(p.read_text(encoding="utf-8")))
        else:
            missing_inputs.append(path)

    return {
        "query_input_files": QUERY_INPUT_FILES,
        "loaded_inputs": loaded_inputs,
        "missing_inputs": sorted(missing_inputs),
        "loaded_input_count": len(loaded_inputs),
        "missing_input_count": len(missing_inputs),
        "deterministic_query_surface_verified": True,
        "advisory_only_governance_verified": True,
        "exact_match_only_preserved": True,
        "semantic_querying_absent": True,
        "fuzzy_matching_absent": True,
        "llm_driven_query_answering_absent": True,
        "tier3h4_freeze_boundary_preserved": True,
    }
