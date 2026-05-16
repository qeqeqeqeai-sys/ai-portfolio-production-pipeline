-- Tier 3H — Advisory Transmission Candidate Discovery (isolated/advisory-only)

create extension if not exists pgcrypto;

create table if not exists public.tier3h_transmission_candidates (
  id uuid primary key default gen_random_uuid(),
  run_date_sgt date not null,
  candidate_symbol text not null,
  candidate_name text,
  asset_class text,
  discovery_theme text not null,
  candidate_source text not null,
  positive_transmission_score numeric not null default 0,
  negative_transmission_score numeric not null default 0,
  net_transmission_score numeric not null default 0,
  evidence_count integer not null default 0,
  confidence_score numeric not null default 0,
  discovery_reason text,
  recommended_action text not null,
  status text not null default 'advisory_only',
  snapshot_id text,
  created_at timestamptz not null default now(),
  constraint tier3h_transmission_candidates_uq
    unique (run_date_sgt, candidate_symbol, discovery_theme, candidate_source),
  constraint tier3h_transmission_candidates_recommended_action_chk
    check (recommended_action in ('watch', 'review', 'candidate_add', 'reject')),
  constraint tier3h_transmission_candidates_status_chk
    check (status = 'advisory_only')
);

create index if not exists idx_tier3h_candidates_run_date_sgt
  on public.tier3h_transmission_candidates (run_date_sgt);
create index if not exists idx_tier3h_candidates_symbol
  on public.tier3h_transmission_candidates (candidate_symbol);
create index if not exists idx_tier3h_candidates_theme
  on public.tier3h_transmission_candidates (discovery_theme);
create index if not exists idx_tier3h_candidates_confidence
  on public.tier3h_transmission_candidates (confidence_score);
create index if not exists idx_tier3h_candidates_recommended_action
  on public.tier3h_transmission_candidates (recommended_action);
