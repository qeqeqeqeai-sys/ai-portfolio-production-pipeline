import os
import sys
from datetime import datetime, timezone
from graph_supabase_client import SupabaseRestClient

PIPELINE_NAME = "PHASE_4D_DAILY_GRAPH_EVOLUTION"

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def main():
    if len(sys.argv) < 4:
        raise RuntimeError("Usage: write_graph_evolution_phase_event.py PHASE_NAME PHASE_ORDER PHASE_STATUS [ERROR_MESSAGE]")

    phase_name = sys.argv[1]
    phase_order = int(sys.argv[2])
    phase_status = sys.argv[3]
    error_message = sys.argv[4] if len(sys.argv) >= 5 else None

    client = SupabaseRestClient()
    row = {
        "evolution_run_id": int(os.getenv("EVOLUTION_RUN_ID")) if os.getenv("EVOLUTION_RUN_ID") else None,
        "pipeline_name": PIPELINE_NAME,
        "phase_name": phase_name,
        "phase_order": phase_order,
        "phase_status": phase_status,
        "started_at": now_iso() if phase_status == "started" else None,
        "completed_at": now_iso() if phase_status in {"success", "warning", "failed", "skipped"} else None,
        "error_message": error_message,
        "metadata": {
            "github_run_id": os.getenv("GITHUB_RUN_ID"),
            "github_workflow": os.getenv("GITHUB_WORKFLOW"),
            "github_repository": os.getenv("GITHUB_REPOSITORY"),
            "github_branch": os.getenv("GITHUB_REF_NAME"),
        },
    }
    client.insert("structural_theme_graph_evolution_phase_events", [row], return_rows=False)

if __name__ == "__main__":
    main()
