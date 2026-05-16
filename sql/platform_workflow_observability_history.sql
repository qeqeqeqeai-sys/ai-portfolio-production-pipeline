-- Tier 3G — Historical Operational Intelligence
-- Advisory table schema for persisting workflow observability snapshots.
-- Apply manually in Supabase SQL editor before enabling persistence writes.

create table if not exists public.platform_workflow_observability_history (
    id bigserial primary key,

    run_date_sgt date,
    workflow_name text,
    run_id text,
    repository text,
    branch_name text,
    run_mode text,
    theme_name text,

    pipeline_status text,
    validation_status text,
    runtime_seconds numeric,
    warnings_count integer,
    errors_count integer,
    hard_fail_count integer,

    health_score numeric,
    trend_regime text,
    runtime_drift_regime text,
    execution_consistency text,

    execution_context jsonb,
    validation_summary jsonb,
    telemetry_context_snapshot jsonb,
    platform_operational_summary jsonb,
    platform_operational_trend_summary jsonb,
    platform_workflow_health_score jsonb,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create unique index if not exists idx_platform_workflow_observability_history_run
    on public.platform_workflow_observability_history (workflow_name, run_id);

create index if not exists idx_platform_workflow_observability_history_date
    on public.platform_workflow_observability_history (run_date_sgt);

create index if not exists idx_platform_workflow_observability_history_workflow_date
    on public.platform_workflow_observability_history (workflow_name, run_date_sgt);

create index if not exists idx_platform_workflow_observability_history_status
    on public.platform_workflow_observability_history (pipeline_status, validation_status);

comment on table public.platform_workflow_observability_history is
'Tier 3G historical observability persistence table for GitHub Actions workflow telemetry, validation, runtime drift, and health scoring snapshots.';
