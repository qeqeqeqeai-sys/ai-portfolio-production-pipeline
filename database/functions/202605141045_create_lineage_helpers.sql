-- Tier 2: Data Contract & Dependency Governance Layer
-- Helper functions for pipeline_run_lineage.
-- Generated: 2026-05-14

create or replace function public.mark_pipeline_run_started(
    p_run_id text,
    p_workflow_name text,
    p_phase text default null,
    p_runtime_layer text default 'unknown',
    p_run_mode text default 'production',
    p_source_tables jsonb default '[]'::jsonb,
    p_metadata jsonb default '{}'::jsonb
)
returns void
language plpgsql
as $$
begin
    insert into public.pipeline_run_lineage (
        run_id,
        workflow_name,
        phase,
        runtime_layer,
        run_mode,
        status,
        source_tables,
        metadata
    ) values (
        p_run_id,
        p_workflow_name,
        p_phase,
        p_runtime_layer,
        p_run_mode,
        'started',
        p_source_tables,
        p_metadata
    )
    on conflict (run_id) do update set
        workflow_name = excluded.workflow_name,
        phase = excluded.phase,
        runtime_layer = excluded.runtime_layer,
        run_mode = excluded.run_mode,
        status = 'started',
        source_tables = excluded.source_tables,
        metadata = excluded.metadata,
        started_at = now(),
        completed_at = null,
        updated_at = now();
end;
$$;

create or replace function public.mark_pipeline_run_completed(
    p_run_id text,
    p_status text,
    p_tables_written jsonb default '[]'::jsonb,
    p_row_counts jsonb default '{}'::jsonb,
    p_dependency_status text default 'checked',
    p_error_class text default null,
    p_error_message text default null,
    p_metadata jsonb default '{}'::jsonb
)
returns void
language plpgsql
as $$
begin
    update public.pipeline_run_lineage
    set
        status = p_status,
        tables_written = p_tables_written,
        row_counts = p_row_counts,
        dependency_status = p_dependency_status,
        error_class = p_error_class,
        error_message = p_error_message,
        metadata = pipeline_run_lineage.metadata || p_metadata,
        completed_at = now(),
        updated_at = now()
    where run_id = p_run_id;
end;
$$;
