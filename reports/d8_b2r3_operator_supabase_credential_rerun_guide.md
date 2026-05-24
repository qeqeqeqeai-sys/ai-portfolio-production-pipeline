# D8.B2-R3 Operator Supabase Credential Injection & Safe Rerun Guide

## Required environment variables
Accepted variables:
- `SUPABASE_URL`
- one of:
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `SUPABASE_ANON_KEY`
  - `SUPABASE_KEY`

Known project URL:
- `SUPABASE_URL=https://townuneetjhcxdznzbht.supabase.co`

## Safe credential export examples (placeholders only)
```bash
export SUPABASE_URL="https://townuneetjhcxdznzbht.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="<REDACTED_SERVICE_ROLE_KEY>"
# OR
export SUPABASE_ANON_KEY="<REDACTED_ANON_KEY>"
# OR
export SUPABASE_KEY="<REDACTED_GENERIC_KEY>"
```

## Hard warnings
- Never commit secrets.
- Never paste service-role keys into reports, logs, commits, PRs, or tickets.
- This flow is strictly read-only diagnostics: no writes, updates, deletes, upserts, or backfill execution.

## Harness command
```bash
python scripts/run_d8_b2r_real_supabase_diagnostics.py
```

The harness updates:
- `reports/d8_b2r_real_supabase_diagnostics_status_report.md`

## Expected status transitions
After valid credentials are injected, expected progression from prior blocked state:
- `BLOCKED_MISSING_CREDENTIALS` → `SOURCE_READY`
- or `SOURCE_EMPTY_BUT_VALID`
- or `SOURCE_BLOCKED_TABLE_MISMATCH`
- or `SOURCE_BLOCKED_SHAPE_MISMATCH`
- or `SOURCE_BLOCKED_NO_CANDIDATES`

## Secret-safety and deterministic governance
- Output contains presence flags and short non-reversible fingerprints only.
- Raw key values are never printed.
- Environment is never dumped.
- No connection strings with secrets are emitted.
- Report includes timestamp, statuses, table accessibility, row counts, candidate counts, rejection IDs/reasons, and explicit no-write confirmation.
