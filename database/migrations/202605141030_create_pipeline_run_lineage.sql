-- Tier 2: Data Contract & Dependency Governance Layer
-- Migration: create pipeline_run_lineage
-- Generated: 2026-05-14
-- Purpose: Additive lineage table for workflow/phase dependency visibility.

create table if not exists public.pipeline_run_lineage (
    id bigint generated always as identity primary key,
    run_id text not null,
    parent_run_id text null,
    workflow_name text not null,
    phase text null,
    runtime_layer text not null default 'unknown',
    run_mode text not null default 'production',
    status text not null default 'started',
    run_date_sgt date not null default ((now() at time zone 'Asia/Singapore'))::date,
    started_at timestamptz not null default now(),
    completed_at timestamptz null,
    source_tables jsonb not null default '[]'::jsonb,
    tables_written jsonb not null default '[]'::jsonb,
    row_counts jsonb not null default '{}'::jsonb,
    dependency_status text not null default 'not_checked',
    error_class text null,
    error_message text null,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint pipeline_run_lineage_run_id_key unique (run_id),
    constraint pipeline_run_lineage_runtime_layer_check check (
        runtime_layer in ('github_actions', 'n8n', 'python', 'manual', 'streamlit', 'unknown')
    ),
    constraint pipeline_run_lineage_run_mode_check check (
        run_mode in ('production', 'research', 'backfill', 'replay', 'manual', 'test')
    ),
    constraint pipeline_run_lineage_status_check check (
        status in ('started', 'dependency_check_failed', 'running', 'success', 'partial_success', 'failed', 'skipped')
    )
);

create index if not exists idx_pipeline_run_lineage_run_date
    on public.pipeline_run_lineage (run_date_sgt desc);

create index if not exists idx_pipeline_run_lineage_workflow_date
    on public.pipeline_run_lineage (workflow_name, run_date_sgt desc);

create index if not exists idx_pipeline_run_lineage_phase_date
    on public.pipeline_run_lineage (phase, run_date_sgt desc);

create index if not exists idx_pipeline_run_lineage_status
    on public.pipeline_run_lineage (status);

create index if not exists idx_pipeline_run_lineage_parent_run_id
    on public.pipeline_run_lineage (parent_run_id);

create index if not exists idx_pipeline_run_lineage_tables_written_gin
    on public.pipeline_run_lineage using gin (tables_written);

create index if not exists idx_pipeline_run_lineage_source_tables_gin
    on public.pipeline_run_lineage using gin (source_tables);

comment on table public.pipeline_run_lineage is
'Governance lineage table linking workflow/phase runs to upstream dependencies, output tables, row counts, and run status.';

comment on column public.pipeline_run_lineage.run_id is
'Unique identifier for one workflow or phase execution.';

comment on column public.pipeline_run_lineage.parent_run_id is
'Optional upstream run_id used to link dependent runs.';

comment on column public.pipeline_run_lineage.source_tables is
'JSON array of upstream table names read by this run.';

comment on column public.pipeline_run_lineage.tables_written is
'JSON array of output table names written by this run.';

comment on column public.pipeline_run_lineage.row_counts is
'JSON object mapping output table names to row counts.';
