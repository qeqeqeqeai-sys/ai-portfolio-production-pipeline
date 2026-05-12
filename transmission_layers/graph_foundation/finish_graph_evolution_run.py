import os
import sys
from graph_supabase_client import SupabaseRestClient

PHASE_COLUMNS = {
    "phase3a1": "phase3a1_status",
    "phase3a": "phase3a_status",
    "phase3a2": "phase3a2_status",
    "phase3b": "phase3b_status",
    "phase3c": "phase3c_status",
    "phase3d": "phase3d_status",
    "phase3e": "phase3e_status",
    "phase4a": "phase4a_status",
    "phase4b": "phase4b_status",
}

def main():
    status_map = {}
    for arg in sys.argv[1:]:
        if "=" in arg:
            k, v = arg.split("=", 1)
            status_map[k] = v

    phases = list(PHASE_COLUMNS.keys())
    succeeded = sum(1 for p in phases if status_map.get(p) == "success")
    failed = sum(1 for p in phases if status_map.get(p) == "failed")
    skipped = sum(1 for p in phases if status_map.get(p) == "skipped")
    started = len([p for p in phases if status_map.get(p)])

    if failed > 0 and succeeded > 0:
        final_status = "partial_success"
        checkpoint_status = "checkpointed"
    elif failed > 0:
        final_status = "failed"
        checkpoint_status = "failed"
    elif succeeded == len(phases):
        final_status = "success"
        checkpoint_status = "completed"
    else:
        final_status = "warning"
        checkpoint_status = "checkpointed"

    failure_phase = None
    for p in phases:
        if status_map.get(p) == "failed":
            failure_phase = p
            break

    update = {
        "status": final_status,
        "checkpoint_status": checkpoint_status,
        "phases_started": started,
        "phases_succeeded": succeeded,
        "phases_failed": failed,
        "phases_skipped": skipped,
        "failure_phase": failure_phase,
        "evolution_metadata": {
            "phase": "4D",
            "phase_statuses": status_map,
            "checkpoint_safe": True,
        },
    }

    for p, col in PHASE_COLUMNS.items():
        update[col] = status_map.get(p)

    client = SupabaseRestClient()
    run_id = os.getenv("EVOLUTION_RUN_ID")
    if run_id:
        client.update("structural_theme_graph_evolution_runs", {"id": f"eq.{run_id}"}, update, return_rows=False)
    else:
        client.insert("structural_theme_graph_evolution_runs", [update], return_rows=False)

if __name__ == "__main__":
    main()
