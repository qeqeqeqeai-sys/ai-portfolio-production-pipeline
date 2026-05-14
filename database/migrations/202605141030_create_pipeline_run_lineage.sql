-- 202605141030_create_pipeline_run_lineage.sql
-- Tier 2 Data Contract & Dependency Governance
-- Purpose: create additive run lineage infrastructure for workflow/run dependency tracking.
-- Safe posture: additive DDL, conservative RLS enabled, no destructive operations.

create table if not exists public.pipeline_run_lineage (
    id bigint generated always as identity primary key,

    run_id text not null unique,
    parent_run_id text null,

    workflow_name text not null,
    phase text null,
    runtime_layer text not null default 'unknown',
    run_mode text not null default 'scheduled',
    status text not null default 'started',
    dependency_status text not null default 'unknown',

    run_date_sgt date not null default ((now() at time zone 'Asia/Singapore')::date),
    started_at timestamptz not null default now(),
    completed_at timestamptz null,
    latency_ms bigint null,

    upstream_workflows text[] not null default array[]::text[],
    upstream_tables text[] not null default array[]::text[],
    downstream_tables text[] not null default array[]::text[],
    tables_written text[] not null default array[]::text[],

    row_count bigint null,
    expected_row_count bigint null,
    freshness_reference_at timestamptz null,

    error_class text null,
    error_message text null,
    metadata jsonb not null default '{}'::jsonb,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    constraint pipeline_run_lineage_runtime_layer_chk check (
        runtime_layer in (
            'github_actions',
            'n8n',
            'python',
            'supabase',
            'streamlit',
            'manual',
            'unknown'
        )
    ),

    constraint pipeline_run_lineage_run_mode_chk check (
        run_mode in (
            'scheduled',
            'manual',
            'backfill',
            'replay',
            'validation',
            'test',
            'unknown'
        )
    ),

    constraint pipeline_run_lineage_status_chk check (
        status in (
            'started',
            'running',
            'completed',
            'failed',
            'skipped',
            'cancelled',
            'unknown'
        )
    ),

    constraint pipeline_run_lineage_dependency_status_chk check (
        dependency_status in (
            'not_checked',
            'unknown',
            'fresh',
            'stale',
            'partial',
            'missing',
            'failed',
            'not_applicable'
        )
    ),

    constraint pipeline_run_lineage_latency_nonnegative_chk check (
        latency_ms is null or latency_ms >= 0
    ),

    constraint pipeline_run_lineage_row_count_nonnegative_chk check (
        row_count is null or row_count >= 0
    ),

    constraint pipeline_run_lineage_expected_row_count_nonnegative_chk check (
        expected_row_count is null or expected_row_count >= 0
    )
);

create index if not exists idx_pipeline_run_lineage_run_id
    on public.pipeline_run_lineage (run_id);

create index if not exists idx_pipeline_run_lineage_parent_run_id
    on public.pipeline_run_lineage (parent_run_id);

create index if not exists idx_pipeline_run_lineage_workflow_date
    on public.pipeline_run_lineage (workflow_name, run_date_sgt desc);

create index if not exists idx_pipeline_run_lineage_status_date
    on public.pipeline_run_lineage (status, run_date_sgt desc);

create index if not exists idx_pipeline_run_lineage_runtime_layer_date
    on public.pipeline_run_lineage (runtime_layer, run_date_sgt desc);

create index if not exists idx_pipeline_run_lineage_started_at
    on public.pipeline_run_lineage (started_at desc);

create index if not exists idx_pipeline_run_lineage_tables_written_gin
    on public.pipeline_run_lineage using gin (tables_written);

create index if not exists idx_pipeline_run_lineage_upstream_tables_gin
    on public.pipeline_run_lineage using gin (upstream_tables);

create index if not exists idx_pipeline_run_lineage_downstream_tables_gin
    on public.pipeline_run_lineage using gin (downstream_tables);

create index if not exists idx_pipeline_run_lineage_metadata_gin
    on public.pipeline_run_lineage using gin (metadata);

-- Keep updated_at current for direct updates.
create or replace function public.set_pipeline_run_lineage_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists trg_pipeline_run_lineage_updated_at on public.pipeline_run_lineage;

create trigger trg_pipeline_run_lineage_updated_at
before update on public.pipeline_run_lineage
for each row
execute function public.set_pipeline_run_lineage_updated_at();

-- Conservative security posture:
-- This table contains operational metadata and may include error messages or payload metadata.
-- Enable RLS immediately. Service role bypasses RLS in Supabase; anon/authenticated access should be granted only deliberately later.
alter table public.pipeline_run_lineage enable row level security;

-- Remove broad client grants if they exist. Backend/service-role operations remain possible via service role.
revoke all on table public.pipeline_run_lineage from anon;
revoke all on table public.pipeline_run_lineage from authenticated;

comment on table public.pipeline_run_lineage is
'Tier 2 governance table for workflow/run lineage, dependency freshness, downstream table writes, and operational metadata. RLS enabled by default; intended for backend/service-role use unless explicit read policies are added.';

comment on column public.pipeline_run_lineage.run_id is 'Unique run identifier supplied by GitHub Actions, n8n, Python, or manual run wrapper.';
comment on column public.pipeline_run_lineage.parent_run_id is 'Optional parent/triggering run ID for lineage chaining.';
comment on column public.pipeline_run_lineage.dependency_status is 'Controlled dependency/freshness status: not_checked, unknown, fresh, stale, partial, missing, failed, not_applicable.';
comment on column public.pipeline_run_lineage.metadata is 'Non-secret JSON metadata. Do not store credentials, tokens, raw API keys, or sensitive payloads.';
