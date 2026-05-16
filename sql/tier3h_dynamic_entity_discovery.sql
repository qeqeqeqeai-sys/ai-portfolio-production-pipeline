-- Tier 3H.4A — Dynamic Structural Entity Discovery (advisory-only scaffold)

create extension if not exists pgcrypto;

create table if not exists public.tier3h_dynamic_entity_discovery (
  id uuid primary key default gen_random_uuid(),
  run_date_sgt date not null,
  theme_name text not null,
  source_node text,
  target_node text,
  propagation_context_id text,
  candidate_asset_id text not null,
  candidate_name text,
  candidate_type text,
  ticker text,
  exchange text,
  discovery_method text not null,
  evidence_sources jsonb not null default '[]'::jsonb,
  evidence_count integer not null default 0,
  source_quality_score numeric not null default 0,
  thematic_relevance_score numeric not null default 0,
  entity_resolution_score numeric not null default 0,
  cross_source_score numeric not null default 0,
  candidate_confidence_score numeric not null default 0,
  candidate_confidence_band text not null,
  confidence_explanation text,
  advisory_status text not null default 'advisory_review',
  rejection_reason text,
  llm_used boolean not null default false,
  llm_model text,
  llm_classification_json jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint tier3h_dynamic_entity_discovery_uq
    unique (run_date_sgt, theme_name, candidate_asset_id, discovery_method),
  constraint tier3h_dynamic_entity_discovery_confidence_band_chk
    check (candidate_confidence_band in ('high_confidence', 'medium_confidence', 'low_confidence', 'rejected_or_noise')),
  constraint tier3h_dynamic_entity_discovery_advisory_status_chk
    check (advisory_status in ('advisory_review', 'advisory_rejected')),
  constraint tier3h_dynamic_entity_discovery_llm_guardrail_chk
    check (llm_used = false)
);

create index if not exists idx_tier3h4_dynamic_run_date_sgt
  on public.tier3h_dynamic_entity_discovery (run_date_sgt);
create index if not exists idx_tier3h4_dynamic_theme_name
  on public.tier3h_dynamic_entity_discovery (theme_name);
create index if not exists idx_tier3h4_dynamic_candidate_asset_id
  on public.tier3h_dynamic_entity_discovery (candidate_asset_id);
create index if not exists idx_tier3h4_dynamic_confidence_band
  on public.tier3h_dynamic_entity_discovery (candidate_confidence_band);
create index if not exists idx_tier3h4_dynamic_advisory_status
  on public.tier3h_dynamic_entity_discovery (advisory_status);
