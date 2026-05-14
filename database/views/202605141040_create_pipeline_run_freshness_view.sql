-- Tier 2: Data Contract & Dependency Governance Layer
-- View: pipeline_run_freshness_v
-- Generated: 2026-05-14
-- Purpose: Simple freshness visibility over pipeline_run_lineage.

create or replace view public.pipeline_run_freshness_v as
select
    workflow_name,
    phase,
    runtime_layer,
    run_mode,
    run_date_sgt,
    status,
    dependency_status,
    started_at,
    completed_at,
    extract(epoch from (now() - coalesce(completed_at, started_at))) / 60.0 as age_minutes,
    source_tables,
    tables_written,
    row_counts,
    error_class,
    error_message,
    metadata
from public.pipeline_run_lineage
where id in (
    select distinct on (coalesce(phase, workflow_name), workflow_name)
        id
    from public.pipeline_run_lineage
    order by coalesce(phase, workflow_name), workflow_name, started_at desc
);

comment on view public.pipeline_run_freshness_v is
'Latest lineage status per workflow/phase for dependency freshness dashboards and preflight checks.';
