-- Tier 3H.4B — Tavily Dynamic Entity Evidence (advisory-only)

create extension if not exists pgcrypto;

create table if not exists public.tier3h_dynamic_entity_evidence (
  id uuid primary key default gen_random_uuid(),
  run_date_sgt date not null,
  theme_name text not null,
  source_node text,
  target_node text,
  query_text text not null,
  candidate_asset_id text,
  candidate_name text,
  candidate_ticker text,
  source_url text not null,
  source_domain text,
  source_title text,
  source_snippet text,
  source_rank integer,
  retrieved_at timestamptz not null,
  discovery_method text not null default 'tavily_search',
  evidence_quality_score numeric not null default 0,
  thematic_keyword_matches jsonb not null default '[]'::jsonb,
  matched_entity_terms jsonb not null default '[]'::jsonb,
  suppression_flags jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint tier3h_dynamic_entity_evidence_uq
    unique (run_date_sgt, theme_name, query_text, source_url)
);

create index if not exists idx_tier3h4_evidence_run_date_sgt
  on public.tier3h_dynamic_entity_evidence (run_date_sgt);
create index if not exists idx_tier3h4_evidence_theme_name
  on public.tier3h_dynamic_entity_evidence (theme_name);
create index if not exists idx_tier3h4_evidence_candidate_ticker
  on public.tier3h_dynamic_entity_evidence (candidate_ticker);
create index if not exists idx_tier3h4_evidence_source_domain
  on public.tier3h_dynamic_entity_evidence (source_domain);
create index if not exists idx_tier3h4_evidence_discovery_method
  on public.tier3h_dynamic_entity_evidence (discovery_method);
create index if not exists idx_tier3h4_evidence_quality_score
  on public.tier3h_dynamic_entity_evidence (evidence_quality_score);
