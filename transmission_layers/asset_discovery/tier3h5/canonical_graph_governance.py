from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any


def _canonical_node_identity(candidate: dict[str, Any]) -> tuple[str, str, str | None, str | None]:
    legacy_id = str(candidate.get("candidate_asset_id") or "").strip()
    canonical_propagation_asset_id = str(candidate.get("canonical_propagation_asset_id") or "").strip() or None
    canonical_security_id = str(candidate.get("canonical_security_id") or "").strip() or None
    canonical_issuer_id = str(candidate.get("canonical_issuer_id") or "").strip() or None
    registry_status = str(candidate.get("registry_resolution_status") or "").strip()

    if registry_status == "conflict":
        return legacy_id, "conflict_preserved_legacy", canonical_security_id, canonical_issuer_id
    if registry_status == "invalid_input":
        return legacy_id, "invalid_input_preserved_legacy", canonical_security_id, canonical_issuer_id
    if registry_status == "no_match":
        return legacy_id, "unresolved_preserved_legacy", canonical_security_id, canonical_issuer_id

    if canonical_propagation_asset_id and canonical_propagation_asset_id.startswith("CANONICAL_SECURITY::"):
        return canonical_propagation_asset_id, "canonical_registry_security", canonical_security_id, canonical_issuer_id
    if canonical_propagation_asset_id and canonical_propagation_asset_id.startswith("CANONICAL_ISSUER::"):
        return canonical_propagation_asset_id, "canonical_registry_issuer", canonical_security_id, canonical_issuer_id

    if canonical_security_id:
        return f"CANONICAL_SECURITY::{canonical_security_id}", "canonical_registry_security", canonical_security_id, canonical_issuer_id
    if canonical_issuer_id:
        return f"CANONICAL_ISSUER::{canonical_issuer_id}", "canonical_registry_issuer", canonical_security_id, canonical_issuer_id

    return legacy_id, "legacy_candidate_asset_id", canonical_security_id, canonical_issuer_id


def govern_canonical_graph_edges(
    nodes: list[dict[str, Any]] | None,
    edges: list[dict[str, Any]] | None,
    collapse_duplicates: bool = True,
) -> dict[str, Any]:
    safe_nodes = deepcopy(nodes or [])
    safe_edges = deepcopy(edges or [])

    node_by_legacy_id: dict[str, dict[str, Any]] = {}
    graph_identity_mode_counts: dict[str, int] = {}

    diagnostics: dict[str, Any] = {
        "graph_governance_edges_seen": len(safe_edges),
        "graph_governance_nodes_seen": len(safe_nodes),
        "canonical_graph_nodes_used": 0,
        "legacy_graph_nodes_preserved": 0,
        "canonical_graph_edges_accepted": 0,
        "duplicate_canonical_edges_collapsed": 0,
        "duplicate_canonical_edges_flagged": 0,
        "self_loops_prevented": 0,
        "conflict_edges_preserved_legacy": 0,
        "invalid_edges_preserved_legacy": 0,
        "unresolved_edges_preserved_legacy": 0,
        "graph_identity_mode_counts": {},
        "edge_governance_status_counts": {},
        "canonical_edge_conflict_preventions": 0,
    }

    governed_nodes: list[dict[str, Any]] = []
    for node in safe_nodes:
        legacy_id = str(node.get("candidate_asset_id") or "").strip()
        canonical_graph_node_id, identity_mode, canonical_security_id, canonical_issuer_id = _canonical_node_identity(node)
        row = dict(node)
        row["legacy_candidate_asset_id"] = legacy_id
        row["canonical_graph_node_id"] = canonical_graph_node_id
        row["graph_identity_mode"] = identity_mode
        row["canonical_security_id"] = canonical_security_id
        row["canonical_issuer_id"] = canonical_issuer_id
        governed_nodes.append(row)

        if legacy_id:
            node_by_legacy_id[legacy_id] = row

        graph_identity_mode_counts[identity_mode] = graph_identity_mode_counts.get(identity_mode, 0) + 1
        if identity_mode in {"canonical_registry_security", "canonical_registry_issuer"}:
            diagnostics["canonical_graph_nodes_used"] += 1
        else:
            diagnostics["legacy_graph_nodes_preserved"] += 1

    seen_canonical_edges: dict[str, int] = {}
    edge_status_counts: dict[str, int] = {}
    governed_edges: list[dict[str, Any]] = []

    for edge_index, edge in enumerate(safe_edges):
        source_legacy = str(edge.get("source_asset_id") or edge.get("legacy_source_asset_id") or "").strip()
        target_legacy = str(edge.get("target_asset_id") or edge.get("legacy_target_asset_id") or "").strip()
        row = dict(edge)
        row["legacy_source_asset_id"] = source_legacy
        row["legacy_target_asset_id"] = target_legacy

        source_node = node_by_legacy_id.get(source_legacy, {"canonical_graph_node_id": source_legacy, "graph_identity_mode": "legacy_candidate_asset_id", "canonical_propagation_asset_id": None, "registry_resolution_status": ""})
        target_node = node_by_legacy_id.get(target_legacy, {"canonical_graph_node_id": target_legacy, "graph_identity_mode": "legacy_candidate_asset_id", "canonical_propagation_asset_id": None, "registry_resolution_status": ""})

        source_status = str(source_node.get("registry_resolution_status") or "")
        target_status = str(target_node.get("registry_resolution_status") or "")
        if source_status == "conflict" or target_status == "conflict":
            status = "conflict_preserved_legacy"
            reason = "registry_conflict"
            canonical_source = source_legacy
            canonical_target = target_legacy
            diagnostics["conflict_edges_preserved_legacy"] += 1
        elif source_status == "invalid_input" or target_status == "invalid_input" or not source_legacy or not target_legacy:
            status = "invalid_input_preserved_legacy"
            reason = "invalid_input"
            canonical_source = source_legacy
            canonical_target = target_legacy
            diagnostics["invalid_edges_preserved_legacy"] += 1
        elif source_status == "no_match" or target_status == "no_match":
            status = "legacy_edge_preserved"
            reason = "unresolved_canonical_identity"
            canonical_source = source_legacy
            canonical_target = target_legacy
            diagnostics["unresolved_edges_preserved_legacy"] += 1
        else:
            canonical_source = str(source_node.get("canonical_graph_node_id") or source_legacy)
            canonical_target = str(target_node.get("canonical_graph_node_id") or target_legacy)
            source_mode = source_node.get("graph_identity_mode", "legacy_candidate_asset_id")
            target_mode = target_node.get("graph_identity_mode", "legacy_candidate_asset_id")
            graph_mode = source_mode if source_mode == target_mode else "canonical_mixed"

            if source_legacy != target_legacy and canonical_source == canonical_target:
                status = "self_loop_prevented"
                reason = "canonicalization_created_self_loop"
                row["edge_conflict_status"] = "prevented"
                diagnostics["self_loops_prevented"] += 1
                diagnostics["canonical_edge_conflict_preventions"] += 1
            else:
                canonical_edge_id = f"{canonical_source}-->{canonical_target}"
                if canonical_edge_id in seen_canonical_edges:
                    dup_group = f"DUPLICATE_CANONICAL_EDGE::{canonical_edge_id}"
                    row["edge_duplicate_group_id"] = dup_group
                    diagnostics["canonical_edge_conflict_preventions"] += 1
                    if collapse_duplicates:
                        status = "duplicate_canonical_edge_collapsed"
                        reason = "duplicate_canonical_edge"
                        diagnostics["duplicate_canonical_edges_collapsed"] += 1
                    else:
                        status = "duplicate_canonical_edge_flagged"
                        reason = "duplicate_canonical_edge"
                        diagnostics["duplicate_canonical_edges_flagged"] += 1
                else:
                    seen_canonical_edges[canonical_edge_id] = edge_index
                    status = "canonical_edge_accepted" if graph_mode != "legacy_candidate_asset_id" else "legacy_edge_preserved"
                    reason = "canonical_edge_unique" if status == "canonical_edge_accepted" else "legacy_identity_only"
                    if status == "canonical_edge_accepted":
                        diagnostics["canonical_graph_edges_accepted"] += 1

            row["graph_identity_mode"] = graph_mode

        row["canonical_source_asset_id"] = source_node.get("canonical_propagation_asset_id")
        row["canonical_target_asset_id"] = target_node.get("canonical_propagation_asset_id")
        row["canonical_graph_source_id"] = canonical_source
        row["canonical_graph_target_id"] = canonical_target
        row["canonical_graph_edge_id"] = f"{canonical_source}-->{canonical_target}"
        row["edge_governance_status"] = status
        row["edge_governance_reason"] = reason

        edge_status_counts[status] = edge_status_counts.get(status, 0) + 1

        if status == "duplicate_canonical_edge_collapsed":
            continue
        governed_edges.append(row)

    diagnostics["graph_identity_mode_counts"] = dict(sorted(graph_identity_mode_counts.items()))
    diagnostics["edge_governance_status_counts"] = dict(sorted(edge_status_counts.items()))

    return {"nodes": governed_nodes, "edges": governed_edges, "diagnostics": diagnostics}


def _sample() -> dict[str, Any]:
    nodes = [
        {"candidate_asset_id": "legacy_aapl_1", "canonical_propagation_asset_id": "CANONICAL_SECURITY::sec_aapl", "registry_resolution_status": "accepted"},
        {"candidate_asset_id": "legacy_aapl_2", "canonical_propagation_asset_id": "CANONICAL_SECURITY::sec_aapl", "registry_resolution_status": "accepted"},
        {"candidate_asset_id": "legacy_msft", "canonical_propagation_asset_id": "CANONICAL_SECURITY::sec_msft", "registry_resolution_status": "accepted"},
    ]
    edges = [
        {"source_asset_id": "legacy_aapl_1", "target_asset_id": "legacy_msft", "weight": 0.6},
        {"source_asset_id": "legacy_aapl_2", "target_asset_id": "legacy_msft", "weight": 0.8},
    ]
    return govern_canonical_graph_edges(nodes, edges)


if __name__ == "__main__":
    result = _sample()
    print(json.dumps(result["diagnostics"], indent=2, sort_keys=True))
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    (logs_dir / "tier3h5_canonical_graph_governance_summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )
