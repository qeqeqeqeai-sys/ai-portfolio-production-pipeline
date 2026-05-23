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
- No `push` trigger is configured.
- Execution is explicit and human-initiated.

## Secrets Usage
- Reads credentials from repository secrets only:
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`
- Includes pre-execution validation step that fails safely when either secret is missing.
- Workflow avoids printing secret values.

## Secret Mapping Fix
- Root cause: the validation step checked `SUPABASE_URL` and `SUPABASE_ANON_KEY` shell variables, but secrets were previously mapped only on the execute step, so validation could fail even when repository secrets existed.
- Fix: mapped `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `PYTHONPATH` at the job-level `env`, so both validation and execution steps receive the same environment.
- Why mapping is required: GitHub Actions repository secrets are not implicitly exposed as shell environment variables; each job/step must explicitly map `secrets.*` into `env`.
- No-secret-leakage guarantee: validation output reports only presence status (`present` / `missing`) and never echoes secret values.

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
