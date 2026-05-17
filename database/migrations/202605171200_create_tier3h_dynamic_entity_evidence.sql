-- Tier 3H.4C.3 Phase 1: advisory-only persisted evidence table
create table if not exists public.tier3h_dynamic_entity_evidence (
  id bigserial primary key,
  run_date_sgt date not null,
  workflow_run_id text,
  theme_name text,
  candidate_id text,
  candidate_asset_id text,
  candidate_name text,
  evidence_text text,
  source_url text,
  source_title text,
  source_domain text,
  evidence_type text,
  evidence_rank integer,
  evidence_confidence numeric,
  extracted_ticker text,
  extracted_exchange text,
  extraction_method text,
  extraction_confidence numeric,
  extraction_notes jsonb not null default '{}'::jsonb,
  raw_evidence jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_tier3h_dynamic_entity_evidence_run_date_sgt
  on public.tier3h_dynamic_entity_evidence (run_date_sgt);
create index if not exists idx_tier3h_dynamic_entity_evidence_theme_name
  on public.tier3h_dynamic_entity_evidence (theme_name);
create index if not exists idx_tier3h_dynamic_entity_evidence_candidate_id
  on public.tier3h_dynamic_entity_evidence (candidate_id);
create index if not exists idx_tier3h_dynamic_entity_evidence_candidate_asset_id
  on public.tier3h_dynamic_entity_evidence (candidate_asset_id);
create index if not exists idx_tier3h_dynamic_entity_evidence_candidate_name
  on public.tier3h_dynamic_entity_evidence (candidate_name);
create index if not exists idx_tier3h_dynamic_entity_evidence_extracted_ticker
  on public.tier3h_dynamic_entity_evidence (extracted_ticker);
create index if not exists idx_tier3h_dynamic_entity_evidence_extracted_exchange
  on public.tier3h_dynamic_entity_evidence (extracted_exchange);
create index if not exists idx_tier3h_dynamic_entity_evidence_source_domain
  on public.tier3h_dynamic_entity_evidence (source_domain);
