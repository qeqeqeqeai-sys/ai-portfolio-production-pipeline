from historical_backfill_utils import upsert_rows

CHECKPOINT_TABLE = "structural_theme_reconstruction_checkpoints"


def save_checkpoint(
    process_name,
    last_processed_date,
    rows_written,
    chunk_id,
    runtime_seconds,
    status="SUCCESS"
):

    row = {
        "pipeline_name": "HISTORICAL_SOURCE_STATE_BACKFILL",
        "theme_name": "AI_TRANSMISSION",
        "last_completed_date": last_processed_date,
        "status": status,
        "process_name": process_name,
        "last_processed_date": last_processed_date,
        "rows_written": rows_written,
        "chunk_id": chunk_id,
        "runtime_seconds": runtime_seconds,
        "details": {
            "source": "Phase 2D.2B Historical Source State Backfill Engine",
            "rows_written": rows_written,
            "chunk_id": chunk_id
        }
    }

    upsert_rows(
        CHECKPOINT_TABLE,
        [row],
        on_conflict="pipeline_name,theme_name"
    )
