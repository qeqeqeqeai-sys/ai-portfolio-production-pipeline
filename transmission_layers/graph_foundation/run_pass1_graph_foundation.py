import argparse
import sys
import time

from .supabase_rest_client import SupabaseRestClient
from .ai_anchor_graph_seed import build_ai_anchor_seed
from .graph_snapshot_service import GraphSnapshotService, today_sgt, write_graph_telemetry


def main() -> int:
    parser = argparse.ArgumentParser(
        description="PASS 1 — Generic Multi-Theme Transmission Graph Foundation"
    )
    parser.add_argument("--run-date-sgt", default=today_sgt())
    parser.add_argument("--snapshot-version", default="pass1_v1")
    parser.add_argument("--anchor-theme-name", default="ai")
    args = parser.parse_args()

    started_at = time.time()
    client = SupabaseRestClient()

    try:
        nodes, edges = build_ai_anchor_seed(run_date_sgt=args.run_date_sgt)

        node_rows = [node.to_row() for node in nodes]
        edge_rows = [edge.to_row() for edge in edges]

        service = GraphSnapshotService(client)
        result = service.create_snapshot(
            nodes=node_rows,
            edges=edge_rows,
            run_date_sgt=args.run_date_sgt,
            graph_scope="multi_theme",
            anchor_theme_name=args.anchor_theme_name,
            snapshot_version=args.snapshot_version,
        )

        status = "success"
        if result["validation"]["validation_status"] == "warning":
            status = "warning"
        elif result["validation"]["validation_status"] == "failed":
            status = "failed"

        write_graph_telemetry(
            client=client,
            status=status,
            started_at=started_at,
            snapshot_result=result,
        )

        print("PASS 1 graph foundation completed.")
        print(f"snapshot_id={result['snapshot_id']}")
        print(f"validation_status={result['validation']['validation_status']}")
        print(f"nodes_upserted={result['nodes_upserted']}")
        print(f"edges_upserted={result['edges_upserted']}")
        print(f"edge_history_rows_inserted={result['edge_history_rows_inserted']}")

        return 0 if status in ("success", "warning") else 1

    except Exception as exc:
        try:
            write_graph_telemetry(
                client=client,
                status="failed",
                started_at=started_at,
                error_message=str(exc),
            )
        except Exception:
            pass

        print(f"PASS 1 graph foundation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
