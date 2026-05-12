import os
import time
from datetime import datetime
from typing import Dict, List, Any
from zoneinfo import ZoneInfo

from .supabase_rest_client import SupabaseRestClient
from .graph_validation import validate_graph_rows


SGT = ZoneInfo("Asia/Singapore")


def today_sgt() -> str:
    return datetime.now(SGT).date().isoformat()


def now_sgt_compact() -> str:
    return datetime.now(SGT).strftime("%Y%m%d_%H%M%S")


class GraphSnapshotService:
    def __init__(self, client: SupabaseRestClient) -> None:
        self.client = client

    def create_snapshot(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        run_date_sgt: str,
        graph_scope: str = "multi_theme",
        anchor_theme_name: str = "ai",
        snapshot_version: str = "pass1_v1",
    ) -> Dict[str, Any]:

        validation = validate_graph_rows(nodes, edges)
        snapshot_id = f"{graph_scope}_{anchor_theme_name}_{snapshot_version}_{run_date_sgt}_{now_sgt_compact()}"

        active_nodes = [n for n in nodes if n.get("is_active", True)]
        active_edges = [e for e in edges if e.get("is_active", True)]

        def avg(metric: str):
            values = [float(e.get(metric, 0)) for e in edges]
            return round(sum(values) / len(values), 6) if values else None

        snapshot_row = {
            "snapshot_id": snapshot_id,
            "snapshot_version": snapshot_version,
            "run_date_sgt": run_date_sgt,
            "graph_scope": graph_scope,
            "anchor_theme_name": anchor_theme_name,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "active_node_count": len(active_nodes),
            "active_edge_count": len(active_edges),
            "theme_node_count": sum(1 for n in nodes if n.get("node_type") == "theme"),
            "asset_node_count": sum(1 for n in nodes if n.get("node_type") == "asset"),
            "sector_node_count": sum(1 for n in nodes if n.get("node_type") == "sector"),
            "subsector_node_count": sum(1 for n in nodes if n.get("node_type") == "subsector"),
            "macro_factor_node_count": sum(1 for n in nodes if n.get("node_type") == "macro_factor"),
            "avg_edge_strength": avg("edge_strength"),
            "avg_confidence_score": avg("confidence_score"),
            "avg_evidence_intensity": avg("evidence_intensity"),
            "avg_persistence_score": avg("persistence_score"),
            "validation_status": validation["validation_status"],
            "validation_errors": validation["errors"],
            "validation_warnings": validation["warnings"],
            "checkpoint_status": "validated" if validation["validation_status"] in ("passed", "warning") else "failed",
            "snapshot_metadata": {
                "pass": "PASS_1_GENERIC_GRAPH_FOUNDATION",
                "contains_graph_analytics": False,
                "contains_centrality": False,
                "contains_networkx": False,
            },
        }

        inserted_snapshot = self.client.insert("structural_theme_graph_snapshots", [snapshot_row])

        if validation["validation_status"] == "failed":
            return {
                "snapshot_id": snapshot_id,
                "snapshot_row": snapshot_row,
                "validation": validation,
                "nodes_upserted": 0,
                "edges_upserted": 0,
                "edge_history_rows_inserted": 0,
            }

        upserted_nodes = self.client.upsert(
            "structural_theme_graph_nodes",
            nodes,
            on_conflict="node_key",
        )

        upserted_edges = self.client.upsert(
            "structural_theme_graph_edges",
            edges,
            on_conflict="edge_key",
        )

        history_rows = []
        for edge in edges:
            history_rows.append({
                "snapshot_id": snapshot_id,
                "run_date_sgt": run_date_sgt,
                "edge_key": edge["edge_key"],
                "source_node_key": edge["source_node_key"],
                "target_node_key": edge["target_node_key"],
                "edge_type": edge["edge_type"],
                "theme_name": edge.get("theme_name"),
                "anchor_theme_name": edge.get("anchor_theme_name", anchor_theme_name),
                "edge_strength": edge.get("edge_strength", 0),
                "directional_strength": edge.get("directional_strength", 0),
                "confidence_score": edge.get("confidence_score", 0),
                "evidence_intensity": edge.get("evidence_intensity", 0),
                "persistence_score": edge.get("persistence_score", 0),
                "evidence_count": edge.get("evidence_count", 0),
                "edge_metadata": edge.get("edge_metadata", {}),
                "evidence_summary": edge.get("evidence_summary", {}),
            })

        inserted_history = self.client.insert(
            "structural_theme_graph_edge_history",
            history_rows,
        )

        return {
            "snapshot_id": snapshot_id,
            "snapshot_row": snapshot_row,
            "validation": validation,
            "nodes_upserted": len(upserted_nodes),
            "edges_upserted": len(upserted_edges),
            "edge_history_rows_inserted": len(inserted_history),
        }


def write_graph_telemetry(
    client: SupabaseRestClient,
    status: str,
    started_at: float,
    snapshot_result: Dict[str, Any] = None,
    error_message: str = None,
) -> None:
    snapshot_result = snapshot_result or {}
    snapshot_row = snapshot_result.get("snapshot_row", {})
    validation = snapshot_result.get("validation", {})

    row = {
        "pipeline_name": "MULTI_THEME_GRAPH_PASS1",
        "snapshot_id": snapshot_result.get("snapshot_id"),
        "snapshot_version": snapshot_row.get("snapshot_version"),
        "status": status,
        "nodes_upserted": snapshot_result.get("nodes_upserted", 0),
        "edges_upserted": snapshot_result.get("edges_upserted", 0),
        "edge_history_rows_inserted": snapshot_result.get("edge_history_rows_inserted", 0),
        "validation_status": validation.get("validation_status"),
        "validation_error_count": validation.get("error_count", 0),
        "validation_warning_count": validation.get("warning_count", 0),
        "runtime_seconds": round(time.time() - started_at, 3),
        "github_run_id": os.getenv("GITHUB_RUN_ID"),
        "github_workflow": os.getenv("GITHUB_WORKFLOW"),
        "github_repository": os.getenv("GITHUB_REPOSITORY"),
        "github_branch": os.getenv("GITHUB_REF_NAME"),
        "error_message": error_message,
        "telemetry_metadata": {
            "pass": "PASS_1_GENERIC_GRAPH_FOUNDATION",
            "rest_only": True,
        },
    }

    client.insert("structural_theme_graph_telemetry", [row])
