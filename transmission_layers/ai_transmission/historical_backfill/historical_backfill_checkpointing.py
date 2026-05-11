from historical_backfill_utils import fetch_table, upsert_rows

CHECKPOINT_TABLE = "structural_theme_reconstruction_checkpoints"


def get_checkpoint(process_name):
    rows = fetch_table(
        CHECKPOINT_TABLE,
        filters={
            "process_name": f"eq.{process_name}",
            "order": "updated_at.desc",
            "limit": 1
        }
    )

    if not rows:
        return None

    return rows[0]


def save_checkpoint(
    process_name,
    last_processed_date,
    rows_written,
    chunk_id,
    runtime_seconds,
    status="SUCCESS"
):

    row = {
        "process_name": process_name,
        "last_processed_date": last_processed_date,
        "rows_written": rows_written,
        "chunk_id": chunk_id,
        "runtime_seconds": runtime_seconds,
        "status": status
    }

    upsert_rows(
        CHECKPOINT_TABLE,
        [row],
        on_conflict="process_name"
    )
