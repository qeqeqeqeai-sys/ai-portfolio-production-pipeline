-- 202605141045_create_lineage_helpers.sql
-- Tier 2 Data Contract & Dependency Governance
-- Purpose: helper functions for safely recording and completing pipeline run lineage.

create or replace function public.record_pipeline_run_started(
    p_run_id text,
    p_workflow_name text,
    p_phase text default null,
    p_runtime_layer text default 'unknown',
    p_run_mode text default 'scheduled',
    p_parent_run_id text default null,
    p_upstream_workflows text[] default array[]::text[],
    p_upstream_tables text[] default array[]::text[],
    p_downstream_tables text[] default array[]::text[],
    p_expected_row_count bigint default null,
    p_metadata jsonb default '{}'::jsonb
)
returns public.pipeline_run_lineage
language plpgsql
security definer
set search_path = public
as $$
declare
    v_row public.pipeline_run_lineage;
begin
    if p_run_id is null or length(trim(p_run_id)) = 0 then
        raise exception 'record_pipeline_run_started requires non-empty p_run_id';
    end if;

    if p_workflow_name is null or length(trim(p_workflow_name)) = 0 then
        raise exception 'record_pipeline_run_started requires non-empty p_workflow_name';
    end if;

    insert into public.pipeline_run_lineage (
        run_id,
        parent_run_id,
        workflow_name,
        phase,
        runtime_layer,
        run_mode,
        status,
        dependency_status,
        upstream_workflows,
        upstream_tables,
        downstream_tables,
        expected_row_count,
        metadata,
        started_at
    ) values (
        p_run_id,
        p_parent_run_id,
        p_workflow_name,
        p_phase,
        p_runtime_layer,
        p_run_mode,
        'started',
        'not_checked',
        coalesce(p_upstream_workflows, array[]::text[]),
        coalesce(p_upstream_tables, array[]::text[]),
        coalesce(p_downstream_tables, array[]::text[]),
        p_expected_row_count,
        coalesce(p_metadata, '{}'::jsonb),
        now()
    )
    on conflict (run_id) do update set
        parent_run_id = excluded.parent_run_id,
        workflow_name = excluded.workflow_name,
        phase = excluded.phase,
        runtime_layer = excluded.runtime_layer,
        run_mode = excluded.run_mode,
        status = 'started',
        dependency_status = 'not_checked',
        upstream_workflows = excluded.upstream_workflows,
        upstream_tables = excluded.upstream_tables,
        downstream_tables = excluded.downstream_tables,
        expected_row_count = excluded.expected_row_count,
        metadata = public.pipeline_run_lineage.metadata || excluded.metadata,
        started_at = now(),
        completed_at = null,
        latency_ms = null,
        error_class = null,
        error_message = null,
        updated_at = now()
    returning * into v_row;

    return v_row;
end;
$$;

create or replace function public.mark_pipeline_run_completed(
    p_run_id text,
    p_status text default 'completed',
    p_dependency_status text default 'not_applicable',
    p_tables_written text[] default array[]::text[],
    p_row_count bigint default null,
    p_freshness_reference_at timestamptz default null,
    p_error_class text default null,
    p_error_message text default null,
    p_metadata jsonb default '{}'::jsonb,
    p_raise_if_missing boolean default false
)
returns table (
    run_id text,
    updated boolean,
    final_status text,
    message text
)
language plpgsql
security definer
set search_path = public
as $$
declare
    v_updated_count integer;
begin
    if p_run_id is null or length(trim(p_run_id)) = 0 then
        raise exception 'mark_pipeline_run_completed requires non-empty p_run_id';
    end if;

    update public.pipeline_run_lineage prl
       set status = p_status,
           dependency_status = p_dependency_status,
           tables_written = coalesce(p_tables_written, array[]::text[]),
           row_count = p_row_count,
           freshness_reference_at = p_freshness_reference_at,
           error_class = p_error_class,
           error_message = p_error_message,
           metadata = prl.metadata || coalesce(p_metadata, '{}'::jsonb),
           completed_at = now(),
           latency_ms = greatest(0, floor(extract(epoch from (now() - prl.started_at)) * 1000)::bigint),
           updated_at = now()
     where prl.run_id = p_run_id;

    get diagnostics v_updated_count = row_count;

    if v_updated_count = 0 then
        if p_raise_if_missing then
            raise exception 'pipeline_run_lineage run_id not found: %', p_run_id;
        end if;

        return query select
            p_run_id::text,
            false::boolean,
            null::text,
            format('No pipeline_run_lineage row found for run_id=%s', p_run_id)::text;
        return;
    end if;

    return query select
        p_run_id::text,
        true::boolean,
        p_status::text,
        format('Updated pipeline_run_lineage row for run_id=%s', p_run_id)::text;
end;
$$;

create or replace function public.mark_pipeline_run_failed(
    p_run_id text,
    p_error_class text default 'unknown_error',
    p_error_message text default null,
    p_dependency_status text default 'failed',
    p_metadata jsonb default '{}'::jsonb,
    p_raise_if_missing boolean default false
)
returns table (
    run_id text,
    updated boolean,
    final_status text,
    message text
)
language plpgsql
security definer
set search_path = public
as $$
begin
    return query
    select * from public.mark_pipeline_run_completed(
        p_run_id := p_run_id,
        p_status := 'failed',
        p_dependency_status := p_dependency_status,
        p_tables_written := array[]::text[],
        p_row_count := null,
        p_freshness_reference_at := null,
        p_error_class := p_error_class,
        p_error_message := p_error_message,
        p_metadata := p_metadata,
        p_raise_if_missing := p_raise_if_missing
    );
end;
$$;

comment on function public.record_pipeline_run_started is
'Creates or resets a pipeline_run_lineage row for a run. Intended for backend/service-role use.';

comment on function public.mark_pipeline_run_completed is
'Marks a lineage run as completed/failed/skipped/cancelled and returns whether a row was updated. Use p_raise_if_missing=true in stricter orchestration contexts.';

comment on function public.mark_pipeline_run_failed is
'Convenience wrapper to mark a run as failed with error metadata and a controlled dependency_status.';

-- Conservative grants: do not expose helper functions to anon/authenticated clients by default.
revoke all on function public.record_pipeline_run_started(text, text, text, text, text, text, text[], text[], text[], bigint, jsonb) from anon;
revoke all on function public.record_pipeline_run_started(text, text, text, text, text, text, text[], text[], text[], bigint, jsonb) from authenticated;

revoke all on function public.mark_pipeline_run_completed(text, text, text, text[], bigint, timestamptz, text, text, jsonb, boolean) from anon;
revoke all on function public.mark_pipeline_run_completed(text, text, text, text[], bigint, timestamptz, text, text, jsonb, boolean) from authenticated;

revoke all on function public.mark_pipeline_run_failed(text, text, text, text, jsonb, boolean) from anon;
revoke all on function public.mark_pipeline_run_failed(text, text, text, text, jsonb, boolean) from authenticated;
