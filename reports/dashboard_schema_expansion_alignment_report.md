# Dashboard Schema Expansion Alignment Report

## Observed insert failures
D1 seed writes reached physical `dashboard_*` tables, but Supabase returned missing-column errors:
- `Could not find the 'as_of_sgt' column`
- `Could not find the 'alert_score' column`
- `Could not find the 'sample_data_flag' column`

## Root cause
The deployed dashboard tables were created from a minimal read-path schema and did not include the full canonical column contract used by D1 seed payloads plus O2/O4/O6 artifacts.

## Canonical schema inventory
Canonical inventory is encoded in `build_dashboard_expected_column_inventory()` and includes:
- all O1/O4/O6 operational fields
- D1 seed-write fields (`as_of_sgt`, `sample_data_flag`, `alert_score`, etc.)
- run-manifest contract fields including `run_id`, `checksum`, `sample_data_flag`

## Additive migration approach
Added deterministic additive migration:
- `supabase/migrations/20260523_expand_dashboard_operationalization_schema.sql`
- uses `ALTER TABLE ... ADD COLUMN IF NOT EXISTS ...`
- covers all eight dashboard physical tables
- adds targeted indexes for high-use added fields (`as_of_sgt`, `sample_data_flag`, `alert_score`)

## No-destructive-change guarantees
The migration is additive only:
- no `DROP TABLE`
- no `DROP COLUMN`
- no `TRUNCATE`
- no data rewrites
- preserves existing rows and primary keys

## Expected post-migration behavior
After applying the migration:
- D1 seeding can insert canonical payloads without missing-column failures
- O6 read adapter can read expanded contracts consistently
- O4 view model payload hydration remains contract-aligned

## Final decision
`APPROVED_FOR_DASHBOARD_SCHEMA_EXPANSION_ALIGNMENT`
