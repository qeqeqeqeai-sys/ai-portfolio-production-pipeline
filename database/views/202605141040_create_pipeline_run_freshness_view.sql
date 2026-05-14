-- 202605141040_create_pipeline_run_freshness_view.sql
-- Tier 2 Data Contract & Dependency Governance
-- Purpose: read-oriented freshness/lineage summary view for trusted operational contexts.

create or replace view public.pipeline_run_freshness_v as
select
    prl.run_id,
    prl.parent_run_id,
    prl.workflow_name,
    prl.phase,
    prl.runtime_layer,
    prl.run_mode,
    prl.status,
    prl.dependency_status,
    prl.run_date_sgt,
    prl.started_at,
    prl.completed_at,
    prl.latency_ms,
    prl.upstream_workflows,
    prl.upstream_tables,
    prl.downstream_tables,
    prl.tables_written,
    prl.row_count,
    prl.expected_row_count,
    case
        when prl.expected_row_count is null then null
        when prl.expected_row_count = 0 then null
        when prl.row_count is null then null
        else round((prl.row_count::numeric / nullif(prl.expected_row_count, 0)::numeric) * 100, 2)
    end as row_count_coverage_pct,
    prl.freshness_reference_at,
    case
        when prl.completed_at is null then null
        else round(extract(epoch from (now() - prl.completed_at)) / 60.0, 2)
    end as minutes_since_completed,
    case
        when prl.freshness_reference_at is null then null
        else round(extract(epoch from (now() - prl.freshness_reference_at)) / 60.0, 2)
    end as minutes_since_freshness_reference,
    prl.error_class,
    prl.error_message,
    prl.metadata,
    prl.created_at,
    prl.updated_at
from public.pipeline_run_lineage prl;

comment on view public.pipeline_run_freshness_v is
'Trusted operational view summarizing run lineage, completion state, row coverage, dependency status, freshness timing, and error metadata. Do not expose to anon/client contexts unless reviewed.';

-- Conservative visibility posture. Grant read access only after a deliberate policy decision.
revoke all on public.pipeline_run_freshness_v from anon;
revoke all on public.pipeline_run_freshness_v from authenticated;
