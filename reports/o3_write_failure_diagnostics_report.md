# O3 Write Failure Diagnostics Report

## Observed failure
D1 dashboard sample seed executes O3 writes against physical `dashboard_*` tables, but all table writes can return `failed` without deterministic per-table root-cause fields.

## Diagnostic gap
Existing output only exposed coarse status and a generic bounded error string, which was insufficient to quickly classify failures (column mismatch, NOT NULL, unique conflicts, RLS, payload mismatch, etc.).

## Fields added
Per-table diagnostics now include:
- `table_name`
- `status`
- `planned_row_count`
- `attempted_row_count`
- `inserted_or_affected_row_count` (best-effort)
- `error_type`
- `error_message_short`
- `missing_payload_columns`
- `extra_payload_columns`
- `schema_expected_columns`
- `payload_sample_keys`

The runner now prints a `write_result_statuses_detailed=` section with table-level detail rows.

## No-secret-leakage controls
- Error messages are truncated to a bounded length.
- Known sensitive substrings are redacted in error summaries.
- Runner output prints safe keys metadata only (no full payload records, no secrets, no keys).

## Expected next troubleshooting output
On failure, each table row now carries deterministic `error_type` plus bounded `error_message_short` and column-diff context, enabling immediate classification for:
- schema/column mismatch
- NOT NULL violations
- PK/unique conflicts
- data-type issues
- RLS/policy failures
- Supabase insert/upsert API issues

Decision: `APPROVED_FOR_O3_WRITE_FAILURE_DIAGNOSTICS`.
