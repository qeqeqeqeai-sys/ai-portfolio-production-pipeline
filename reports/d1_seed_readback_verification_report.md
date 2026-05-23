# D1 Seed Readback Verification Report

## Observed Issue
GitHub Actions could report `execution_status=completed` while Streamlit diagnostics still showed `row_count=0` across canonical dashboard tables.

## Why Service Role Can Be Needed for Backend Seeding
Controlled backend seeding may require permissions beyond anonymous read-only policy scope. This update allows the runner to prefer `SUPABASE_SERVICE_ROLE_KEY` for backend write execution in CI while preserving bounded deterministic behavior.

## Why Streamlit Should Remain Anonymous / Read-Only
Streamlit remains a read-only display layer and should continue using `SUPABASE_ANON_KEY` for least-privilege access and diagnostics-safe rendering behavior.

## Readback Verification Behavior
When `--execute --verify-readback` is used:
- The seed runner prints execution status, planned counts, write statuses, and post-write per-table readback counts.
- Readback reports status per table: `ready`, `empty`, `query_failed`, or `permission_denied`.
- Verification status is emitted as one of:
  - `verified_non_empty`
  - `verified_empty`
  - `verification_failed`
- If all tables are empty (or verification fails) after execute+verify, the runner exits non-zero.

## Safe Project Fingerprint
The runner logs only a safe project host fingerprint derived from `SUPABASE_URL` (e.g., `<project-ref>.supabase.co`) and never logs secrets.

## No-Secret-Leakage Guarantees
- No credential values are printed.
- Workflow logs only `credential_source` and presence/missing diagnostics.
- Verification output contains only table-level counts and statuses.

## Expected Post-Fix Workflow Result
GitHub workflow now executes:
`python scripts/run_d1_dashboard_sample_seed.py --execute --verify-readback`
with service-role preference when configured.

**Decision:** `APPROVED_FOR_D1_SEED_READBACK_VERIFICATION_AND_BACKEND_KEY_SUPPORT`
