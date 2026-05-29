-- DB-1: append-only SEFI historical read model. Creates schema only; no destructive operations.

create function public.prevent_sefi_read_model_mutation()
returns trigger
language plpgsql
as $$
begin
  raise exception 'SEFI history read-model rows are append-only';
end;
$$;

create table if not exists public.sefi_artifact_registry (
  artifact_id text primary key,
  source_artifact_path text not null,
  source_artifact_sha256 text not null check (source_artifact_sha256 ~ '^[0-9a-f]{64}$'),
  artifact_kind text not null,
  schema_version text,
  created_at timestamptz not null default now(),
  loaded_at timestamptz not null default now(),
  payload_jsonb jsonb not null default '{}'::jsonb,
  duplicate_prevention_key text not null unique,
  check (octet_length(payload_jsonb::text) <= 8192),
  unique (source_artifact_path, source_artifact_sha256)
);

create table if not exists public.sefi_run_registry (
  run_id text primary key,
  phase_id text not null,
  phase_name text not null,
  artifact_id text not null references public.sefi_artifact_registry (artifact_id),
  status text not null,
  created_at timestamptz not null default now(),
  loaded_at timestamptz not null default now(),
  completed_at text,
  payload_jsonb jsonb not null default '{}'::jsonb,
  duplicate_prevention_key text not null unique,
  check (octet_length(payload_jsonb::text) <= 8192)
);

create table if not exists public.sefi_phase_runs (
  id bigserial primary key,
  phase_id text not null,
  phase_name text not null,
  status text not null,
  artifact_id text not null references public.sefi_artifact_registry (artifact_id),
  run_id text not null references public.sefi_run_registry (run_id),
  created_at timestamptz not null default now(),
  loaded_at timestamptz not null default now(),
  completed_at text,
  payload_jsonb jsonb not null default '{}'::jsonb,
  duplicate_prevention_key text not null unique,
  check (octet_length(payload_jsonb::text) <= 8192)
);

create table if not exists public.sefi_hist_observations (
  id bigserial primary key,
  phase_id text not null,
  phase_name text not null,
  observation_type text not null,
  observed_at text,
  artifact_id text not null references public.sefi_artifact_registry (artifact_id),
  run_id text not null references public.sefi_run_registry (run_id),
  created_at timestamptz not null default now(),
  loaded_at timestamptz not null default now(),
  payload_jsonb jsonb not null default '{}'::jsonb,
  duplicate_prevention_key text not null unique,
  check (octet_length(payload_jsonb::text) <= 8192)
);

create table if not exists public.sefi_window_metrics (
  id bigserial primary key,
  phase_id text not null,
  phase_name text not null,
  window_days integer not null check (window_days > 0),
  completeness numeric,
  replay_density numeric,
  replay_saturation numeric,
  contradiction_burden numeric,
  sector_hhi numeric,
  subsector_hhi numeric,
  effective_symbol_count integer,
  artifact_id text not null references public.sefi_artifact_registry (artifact_id),
  run_id text not null references public.sefi_run_registry (run_id),
  created_at timestamptz not null default now(),
  loaded_at timestamptz not null default now(),
  payload_jsonb jsonb not null default '{}'::jsonb,
  duplicate_prevention_key text not null unique,
  check (octet_length(payload_jsonb::text) <= 8192)
);

create table if not exists public.sefi_sector_morphology (
  id bigserial primary key,
  phase_id text not null,
  phase_name text not null,
  morphology_type text not null,
  sector text,
  subsector text,
  symbol_count integer,
  symbol_share numeric,
  rank integer,
  artifact_id text not null references public.sefi_artifact_registry (artifact_id),
  run_id text not null references public.sefi_run_registry (run_id),
  created_at timestamptz not null default now(),
  loaded_at timestamptz not null default now(),
  payload_jsonb jsonb not null default '{}'::jsonb,
  duplicate_prevention_key text not null unique,
  check (octet_length(payload_jsonb::text) <= 8192)
);

create table if not exists public.sefi_symbol_metrics (
  id bigserial primary key,
  phase_id text not null,
  phase_name text not null,
  symbol text not null,
  window_days integer,
  metric_type text not null,
  metric_value numeric,
  artifact_id text not null references public.sefi_artifact_registry (artifact_id),
  run_id text not null references public.sefi_run_registry (run_id),
  created_at timestamptz not null default now(),
  loaded_at timestamptz not null default now(),
  payload_jsonb jsonb not null default '{}'::jsonb,
  duplicate_prevention_key text not null unique,
  check (octet_length(payload_jsonb::text) <= 8192)
);

create table if not exists public.sefi_observation_facts (
  id bigserial primary key,
  phase_id text not null,
  phase_name text,
  window_days integer,
  entity_type text not null,
  entity_id text not null,
  metric_name text not null,
  metric_value numeric,
  artifact_id text not null references public.sefi_artifact_registry (artifact_id),
  run_id text not null references public.sefi_run_registry (run_id),
  created_at timestamptz not null default now(),
  loaded_at timestamptz not null default now(),
  payload_jsonb jsonb not null default '{}'::jsonb,
  duplicate_prevention_key text not null unique,
  check (octet_length(payload_jsonb::text) <= 8192)
);

create index if not exists idx_sefi_artifact_registry_sha on public.sefi_artifact_registry (source_artifact_sha256);
create index if not exists idx_sefi_run_registry_phase_loaded on public.sefi_run_registry (phase_id, loaded_at desc);
create index if not exists idx_sefi_phase_runs_phase_loaded on public.sefi_phase_runs (phase_id, loaded_at desc);
create index if not exists idx_sefi_window_metrics_phase_window on public.sefi_window_metrics (phase_id, window_days, loaded_at desc);
create index if not exists idx_sefi_sector_morphology_phase_type on public.sefi_sector_morphology (phase_id, morphology_type, rank);
create index if not exists idx_sefi_symbol_metrics_phase_symbol on public.sefi_symbol_metrics (phase_id, symbol, loaded_at desc);
create index if not exists idx_sefi_observation_facts_lookup on public.sefi_observation_facts (phase_id, window_days, entity_type, entity_id, metric_name);

create trigger sefi_artifact_registry_append_only
before update or delete on public.sefi_artifact_registry
for each row execute function public.prevent_sefi_read_model_mutation();

create trigger sefi_run_registry_append_only
before update or delete on public.sefi_run_registry
for each row execute function public.prevent_sefi_read_model_mutation();

create trigger sefi_phase_runs_append_only
before update or delete on public.sefi_phase_runs
for each row execute function public.prevent_sefi_read_model_mutation();

create trigger sefi_hist_observations_append_only
before update or delete on public.sefi_hist_observations
for each row execute function public.prevent_sefi_read_model_mutation();

create trigger sefi_window_metrics_append_only
before update or delete on public.sefi_window_metrics
for each row execute function public.prevent_sefi_read_model_mutation();

create trigger sefi_sector_morphology_append_only
before update or delete on public.sefi_sector_morphology
for each row execute function public.prevent_sefi_read_model_mutation();

create trigger sefi_symbol_metrics_append_only
before update or delete on public.sefi_symbol_metrics
for each row execute function public.prevent_sefi_read_model_mutation();

create trigger sefi_observation_facts_append_only
before update or delete on public.sefi_observation_facts
for each row execute function public.prevent_sefi_read_model_mutation();
