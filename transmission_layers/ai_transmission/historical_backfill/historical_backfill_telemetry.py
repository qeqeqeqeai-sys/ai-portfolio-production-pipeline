from historical_backfill_utils import upsert_rows

TABLE = "historical_backfill_telemetry"


def write_telemetry(row):
    upsert_rows(
        TABLE,
        [row],
        on_conflict="id"
    )
