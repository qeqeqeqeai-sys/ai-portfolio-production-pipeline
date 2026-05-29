-- Staged SEFI universe DB-readiness only. Does not modify public.ai_stock_universe or active loaders.
create table if not exists public.sefi_observation_universe (
  symbol text not null,
  entity_name text not null,
  entity_type text not null,
  asset_class text not null,
  sector text,
  subsector text,
  ecosystem_group text,
  source_phase text not null,
  universe_version text not null,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint sefi_observation_universe_symbol_version_pk primary key (symbol, universe_version),
  constraint sefi_observation_universe_symbol_not_blank check (length(trim(symbol)) > 0),
  constraint sefi_observation_universe_symbol_upper check (symbol = upper(symbol))
);

create index if not exists idx_sefi_observation_universe_active_symbol
  on public.sefi_observation_universe (is_active, symbol);

create index if not exists idx_sefi_observation_universe_source_version
  on public.sefi_observation_universe (source_phase, universe_version);

create or replace function public.set_sefi_observation_universe_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists trg_set_sefi_observation_universe_updated_at on public.sefi_observation_universe;
create trigger trg_set_sefi_observation_universe_updated_at
before update on public.sefi_observation_universe
for each row execute function public.set_sefi_observation_universe_updated_at();
