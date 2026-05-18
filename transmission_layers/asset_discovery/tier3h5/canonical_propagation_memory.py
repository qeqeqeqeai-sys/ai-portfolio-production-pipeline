from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any


CONFLICT_STATUSES = {"conflict"}
INVALID_STATUSES = {"invalid_input"}
UNRESOLVED_STATUSES = {"no_match", "unresolved"}


def _legacy_memory_edge_id(row: dict[str, Any]) -> str:
    legacy_edge = str(row.get("legacy_edge_id") or "").strip()
    if legacy_edge:
        return legacy_edge
    source = str(row.get("legacy_source_asset_id") or row.get("source_asset_id") or "").strip()
    target = str(row.get("legacy_target_asset_id") or row.get("target_asset_id") or "").strip()
    return f"{source}-->{target}"


def consolidate_canonical_propagation_memory(
    memory_rows: list[dict[str, Any]] | None,
    collapse_duplicates: bool = True,
) -> dict[str, Any]:
    safe_rows = deepcopy(memory_rows or [])
    diagnostics: dict[str, Any] = {
        "memory_governance_records_seen": len(safe_rows),
        "canonical_memory_edges_used": 0,
        "canonical_memory_nodes_used": 0,
        "legacy_memory_records_preserved": 0,
        "duplicate_legacy_memory_collapsed": 0,
        "duplicate_legacy_memory_flagged": 0,
        "canonical_memory_self_loops_prevented": 0,
        "conflict_memory_preserved_legacy": 0,
        "invalid_memory_preserved_legacy": 0,
        "unresolved_memory_preserved_legacy": 0,
        "memory_identity_mode_counts": {},
        "memory_consolidation_status_counts": {},
        "canonical_memory_conflict_preventions": 0,
        "continuity_lineage_consolidations": 0,
        "continuity_lineage_preserved_legacy": 0,
    }

    mode_counts: dict[str, int] = {}
    status_counts: dict[str, int] = {}
    seen_canonical_edges: dict[str, int] = {}
    consolidated: list[dict[str, Any]] = []

    for row_index, memory in enumerate(safe_rows):
        row = dict(memory)
        row["legacy_memory_id"] = str(row.get("legacy_memory_id") or row.get("memory_id") or f"legacy_memory_{row_index}").strip()
        row["legacy_source_asset_id"] = str(row.get("legacy_source_asset_id") or row.get("source_asset_id") or "").strip()
        row["legacy_target_asset_id"] = str(row.get("legacy_target_asset_id") or row.get("target_asset_id") or "").strip()
        row["legacy_edge_id"] = _legacy_memory_edge_id(row)

        source = row["legacy_source_asset_id"]
        target = row["legacy_target_asset_id"]
        canonical_source = str(row.get("canonical_graph_source_id") or "").strip()
        canonical_target = str(row.get("canonical_graph_target_id") or "").strip()
        canonical_graph_edge_id = str(row.get("canonical_graph_edge_id") or "").strip()
        conflict_status = str(row.get("memory_conflict_status") or row.get("registry_resolution_status") or "").strip()

        mode = "legacy_edge"
        status = "legacy_memory_preserved"
        reason = "legacy_fallback"
        continuity = "preserved_legacy"

        if conflict_status in CONFLICT_STATUSES:
            mode = "conflict_preserved_legacy"
            status = "conflict_preserved_legacy"
            reason = "registry_or_graph_conflict"
            diagnostics["conflict_memory_preserved_legacy"] += 1
        elif conflict_status in INVALID_STATUSES or not source or not target:
            mode = "invalid_input_preserved_legacy"
            status = "invalid_input_preserved_legacy"
            reason = "invalid_input"
            diagnostics["invalid_memory_preserved_legacy"] += 1
        elif conflict_status in UNRESOLVED_STATUSES:
            mode = "unresolved_preserved_legacy"
            status = "unresolved_preserved_legacy"
            reason = "unresolved_canonical_identity"
            diagnostics["unresolved_memory_preserved_legacy"] += 1
        else:
            if canonical_graph_edge_id:
                canonical_memory_edge_id = f"CANONICAL_MEMORY_EDGE::{canonical_graph_edge_id}"
                canonical_memory_node_id = None
                mode = "canonical_graph_edge"
                diagnostics["canonical_memory_edges_used"] += 1
            elif canonical_source and canonical_target:
                canonical_memory_edge_id = f"CANONICAL_MEMORY_EDGE::{canonical_source}-->{canonical_target}"
                canonical_memory_node_id = f"CANONICAL_MEMORY_NODE::{canonical_source}|{canonical_target}"
                mode = "canonical_graph_node" if canonical_source == canonical_target else "canonical_mixed"
                diagnostics["canonical_memory_nodes_used"] += 1
            else:
                canonical_memory_edge_id = f"LEGACY_MEMORY_EDGE::{row['legacy_edge_id']}"
                canonical_memory_node_id = None
                mode = "legacy_edge"

            if source != target and canonical_source and canonical_target and canonical_source == canonical_target:
                status = "canonical_self_loop_prevented"
                reason = "canonicalization_created_self_loop"
                row["memory_duplicate_group_id"] = f"SELF_LOOP::{canonical_source}"
                row["memory_conflict_status"] = "prevented"
                diagnostics["canonical_memory_self_loops_prevented"] += 1
                diagnostics["canonical_memory_conflict_preventions"] += 1
            elif mode in {"canonical_graph_edge", "canonical_graph_node", "canonical_mixed"}:
                if canonical_memory_edge_id in seen_canonical_edges:
                    group = f"DUPLICATE_MEMORY::{canonical_memory_edge_id}"
                    row["memory_duplicate_group_id"] = group
                    diagnostics["canonical_memory_conflict_preventions"] += 1
                    if collapse_duplicates:
                        status = "duplicate_legacy_memory_collapsed"
                        reason = "duplicate_canonical_memory_edge"
                        diagnostics["duplicate_legacy_memory_collapsed"] += 1
                        continuity = "consolidated"
                    else:
                        status = "duplicate_legacy_memory_flagged"
                        reason = "duplicate_canonical_memory_edge"
                        diagnostics["duplicate_legacy_memory_flagged"] += 1
                else:
                    seen_canonical_edges[canonical_memory_edge_id] = row_index
                    status = "canonical_memory_accepted"
                    reason = "canonical_memory_unique"
                    continuity = "consolidated"
            else:
                status = "legacy_memory_preserved"
                reason = "canonical_identity_unavailable"

            row["canonical_memory_edge_id"] = canonical_memory_edge_id
            row["canonical_memory_node_id"] = canonical_memory_node_id

        if status in {"legacy_memory_preserved", "conflict_preserved_legacy", "invalid_input_preserved_legacy", "unresolved_preserved_legacy", "canonical_self_loop_prevented", "ambiguous_memory_mapping_preserved_legacy"}:
            diagnostics["legacy_memory_records_preserved"] += 1
            diagnostics["continuity_lineage_preserved_legacy"] += 1
            continuity = "preserved_legacy"
        elif status in {"canonical_memory_accepted", "duplicate_legacy_memory_collapsed", "duplicate_legacy_memory_flagged"}:
            diagnostics["continuity_lineage_consolidations"] += 1

        row["memory_identity_mode"] = mode
        row["memory_consolidation_status"] = status
        row["memory_consolidation_reason"] = reason
        row["continuity_lineage_status"] = continuity

        mode_counts[mode] = mode_counts.get(mode, 0) + 1
        status_counts[status] = status_counts.get(status, 0) + 1

        if status == "duplicate_legacy_memory_collapsed":
            continue
        consolidated.append(row)

    diagnostics["memory_identity_mode_counts"] = dict(sorted(mode_counts.items()))
    diagnostics["memory_consolidation_status_counts"] = dict(sorted(status_counts.items()))

    return {"memory": consolidated, "diagnostics": diagnostics}


def _sample() -> dict[str, Any]:
    return consolidate_canonical_propagation_memory(
        [
            {
                "legacy_memory_id": "m1",
                "legacy_source_asset_id": "legacy_aapl_1",
                "legacy_target_asset_id": "legacy_msft",
                "canonical_graph_source_id": "CANONICAL_SECURITY::sec_aapl",
                "canonical_graph_target_id": "CANONICAL_SECURITY::sec_msft",
                "canonical_graph_edge_id": "CANONICAL_SECURITY::sec_aapl-->CANONICAL_SECURITY::sec_msft",
            },
            {
                "legacy_memory_id": "m2",
                "legacy_source_asset_id": "legacy_aapl_2",
                "legacy_target_asset_id": "legacy_msft",
                "canonical_graph_source_id": "CANONICAL_SECURITY::sec_aapl",
                "canonical_graph_target_id": "CANONICAL_SECURITY::sec_msft",
                "canonical_graph_edge_id": "CANONICAL_SECURITY::sec_aapl-->CANONICAL_SECURITY::sec_msft",
            },
        ]
    )


if __name__ == "__main__":
    result = _sample()
    print(json.dumps(result["diagnostics"], indent=2, sort_keys=True))
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    (logs_dir / "tier3h5_canonical_propagation_memory_summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )
