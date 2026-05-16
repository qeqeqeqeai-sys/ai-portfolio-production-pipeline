create extension if not exists pgcrypto;

create table if not exists public.tier3h_operational_api_usage (
  id uuid primary key default gen_random_uuid(),
  run_date_sgt date not null,
  workflow_name text not null,
  provider text not null,
  api_calls_attempted integer not null default 0,
  api_calls_executed integer not null default 0,
  cache_hits integer not null default 0,
  cache_misses integer not null default 0,
  fallback_events integer not null default 0,
  rate_limit_events integer not null default 0,
  quota_exhaustion_events integer not null default 0,
  retry_events integer not null default 0,
  success_count integer not null default 0,
  failure_count integer not null default 0,
  estimated_cost numeric,
  execution_seconds numeric,
  metadata jsonb,
  created_at timestamptz not null default now(),
  unique (run_date_sgt, workflow_name, provider)
);

create index if not exists idx_tier3h_operational_usage_run_date_sgt
  on public.tier3h_operational_api_usage (run_date_sgt);
create index if not exists idx_tier3h_operational_usage_provider
  on public.tier3h_operational_api_usage (provider);
create index if not exists idx_tier3h_operational_usage_workflow_name
  on public.tier3h_operational_api_usage (workflow_name);

alter table if exists public.tier3h_dynamic_entity_evidence
  add column if not exists cache_reused boolean not null default false;
