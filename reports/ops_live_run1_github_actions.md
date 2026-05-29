# OPS-LIVE-RUN-1 GitHub Actions Implementation Report

## Workflows created

- `.github/workflows/sefi_live_daily.yml` — daily OPS-LIVE-RUN-1 operational accumulation.
- `.github/workflows/sefi_weekly_observation_review.yml` — weekly observation review.
- `.github/workflows/sefi_monthly_ecology_review.yml` — monthly ecology review.
- `.github/workflows/sefi_operational_health.yml` — read-only operational telemetry.

## Schedules chosen

- Daily accumulation: `17 2 * * *` UTC, once per day and not exactly on the hour.
- Weekly observation review: `23 3 * * 1` UTC, Mondays once per week and not exactly on the hour.
- Monthly ecology review: `41 4 3 * *` UTC, third day of each month and not exactly on the hour.
- Operational health: `37 5 * * *` UTC, daily read-only telemetry and not exactly on the hour.

All workflows also support `workflow_dispatch` for manual UTC-safe execution.

## Execution order

- Daily accumulation:
  1. OPS-LIVE-1 controlled ingest via `scripts/run_ops_live1b_50_symbol_operational_ingest.py`.
  2. OPS-LIVE-2 fact accumulation via `scripts/run_ops_live2_observation_fact_accumulation.py`.
  3. OPS-LIVE-3 structural state snapshot via `scripts/run_ops_live3_structural_state_snapshot.py`.
- Weekly observation review:
  1. HIST-LONG-8 cross-window persistence review.
  2. HIST-LONG-9 persistence drift review.
- Monthly ecology review:
  1. HIST-LONG-4 real multi-window ecology.
  2. HIST-LONG-5B temporal delta sensitivity classification.
  3. HIST-LONG-6 cross-sectional ecology differentiation.
  4. HIST-LONG-7 intra-group structural contrast.
- Operational health is read-only and only displays telemetry.

## Assumptions

- The existing Python runtime target is Python 3.11, matching current repository workflows.
- Dependency installation should continue to use root `requirements.txt`.
- Daily OPS-LIVE-RUN-1 accumulation requires `FMP_API_KEY`, `SUPABASE_URL`, and `SUPABASE_SERVICE_ROLE_KEY` or `SUPABASE_KEY` GitHub secrets.
- Monthly HIST-LONG-4 execution requires `FMP_API_KEY`.
- Health telemetry reports unavailable values instead of failing when optional credentials or metrics are absent.

## Operational risks

- Missing or rotated GitHub secrets will fail daily accumulation or monthly ecology preflight before any pipeline step runs.
- Provider API throttling, outage, or malformed responses can fail closed in OPS-LIVE-1 or HIST-LONG-4.
- Supabase connectivity or permission failures can block OPS-LIVE-2 fact persistence and OPS-LIVE-3 readback.
- HIST-LONG-8/HIST-LONG-9 may report blocked review status if required upstream observation artifacts or facts are not yet available.
- GitHub artifact retention is bounded and should not be treated as durable persistence.
