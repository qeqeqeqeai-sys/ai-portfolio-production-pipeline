# GitHub Actions D1 Seed Workflow Report

## Objective
Provide deployment automation support for explicitly controlled execution of the deterministic D1 dashboard sample-data seed runner against Supabase.

## Workflow Scope
- Adds one manual GitHub Actions workflow:
  - `.github/workflows/run-d1-dashboard-seed.yml`
- Executes only:
  - `python scripts/run_d1_dashboard_sample_seed.py --execute`
- Uses existing deterministic/O3-controlled seed path.

## Manual-Trigger-Only Design
- Trigger mode is `workflow_dispatch` only.
- No cron or schedule trigger is configured.
- Execution is explicit and human-initiated.

## Secrets Usage
- Reads credentials from repository secrets only:
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`
- Includes pre-execution validation step that fails safely when either secret is missing.
- Workflow avoids printing secret values.

## Deterministic / O3-Controlled Persistence
- Workflow delegates all write behavior to the existing deterministic D1 runner.
- No new scoring/intelligence logic is introduced.
- No direct SQL execution path is added in the workflow.

## Non-Autonomous Guardrails
- No autonomous scheduling.
- No uncontrolled writes.
- No loops/retries added.
- No random generation paths introduced.

## Post-Seed Expectations
After successful run with valid credentials and reachable tables:
- `runtime_mode=read_only_supabase_mode`
- `payload_source=supabase_snapshot`
- `normalization_status=normalized`
