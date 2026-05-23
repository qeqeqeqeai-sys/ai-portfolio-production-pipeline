# Dashboard O6/O7 Section Read Diagnostics Report

## Observed degraded snapshot
Runtime diagnostics can show `payload_source=fallback_payload` and `normalization_status=snapshot_degraded` while credentials/client are present when one or more Supabase read sections are degraded.

## Likely causes
- Missing table(s)
- Table exists but empty and/or run_id/as_of_date filters exclude rows
- RLS or permission denial
- Schema mismatch (missing/renamed columns)
- Query failure
- O6 snapshot-to-O7 mapping degradation mix

## Diagnostic fields added
- `section_read_diagnostics[]` per section/table
  - `table_name`, `section_name`, `status`, `row_count`
  - `required_columns_present`, `missing_columns`
  - `error_type`, `error_message_short`
  - `filter_applied`, `sample_row_keys`
- Summary lists:
  - `empty_sections`
  - `missing_tables`
  - `permission_denied_tables`
  - `schema_mismatch_tables`
  - `query_failed_tables`

## Health interpretation mapping
- all empty => `tables_exist_but_empty_or_filters_exclude_rows`
- any missing => `dashboard_tables_missing`
- any permission denied => `rls_or_permission_denied`
- any schema mismatch => `dashboard_schema_mismatch`
- any query failed => `supabase_query_failed`
- mixed degraded => `mixed_section_degradation`
- all ready => `supabase_snapshot_healthy`

## No-secret-leakage guarantee
All surfaced error text is short and redacted/truncated. Diagnostics avoid exposing Supabase key/URL values.

## Read-only boundary preserved
No writes were added. Changes are diagnostics/read-boundary visibility only.

## Expected decision
`APPROVED_FOR_O6_O7_SECTION_READ_DIAGNOSTICS`
