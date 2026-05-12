import os
from graph_supabase_client import SupabaseRestClient

PIPELINE_NAME = "PHASE_4D_DAILY_GRAPH_EVOLUTION"

def main():
    client = SupabaseRestClient()
    row = {
        "pipeline_name": PIPELINE_NAME,
        "anchor_theme_name": os.getenv("ANCHOR_THEME_NAME", "ai").strip().lower(),
        "theme_name": os.getenv("THEME_NAME") or None,
        "status": "started",
        "github_run_id": os.getenv("GITHUB_RUN_ID"),
        "github_workflow": os.getenv("GITHUB_WORKFLOW"),
        "github_repository": os.getenv("GITHUB_REPOSITORY"),
        "github_branch": os.getenv("GITHUB_REF_NAME"),
        "checkpoint_status": "started",
        "evolution_metadata": {
            "phase": "4D",
            "mode": "daily_master_orchestration",
            "checkpoint_safe": True,
        },
    }
    inserted = client.insert("structural_theme_graph_evolution_runs", [row], return_rows=True)
    run_id = inserted[0]["id"] if inserted else ""
    print(f"EVOLUTION_RUN_ID={run_id}")

if __name__ == "__main__":
    main()
