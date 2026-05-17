CREATE TABLE IF NOT EXISTS public.tier3h_entity_resolution_audit (
  id bigserial PRIMARY KEY,
  run_date_sgt date NOT NULL,
  workflow_run_id text,
  theme_name text,
  raw_entity_name text,
  normalized_name text,
  candidate_ticker text,
  normalized_ticker text,
  candidate_exchange text,
  normalized_exchange text,
  asset_type_guess text,
  canonical_entity_id text,
  resolution_status text NOT NULL,
  resolution_confidence numeric,
  rules_fired jsonb NOT NULL DEFAULT '[]'::jsonb,
  suppression_reason text,
  evidence_urls jsonb NOT NULL DEFAULT '[]'::jsonb,
  source_count integer NOT NULL DEFAULT 0,
  duplicate_group_key text,
  duplicate_group_size integer NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tier3h_entity_resolution_audit_run_date_sgt
  ON public.tier3h_entity_resolution_audit (run_date_sgt);
CREATE INDEX IF NOT EXISTS idx_tier3h_entity_resolution_audit_theme_name
  ON public.tier3h_entity_resolution_audit (theme_name);
CREATE INDEX IF NOT EXISTS idx_tier3h_entity_resolution_audit_resolution_status
  ON public.tier3h_entity_resolution_audit (resolution_status);
CREATE INDEX IF NOT EXISTS idx_tier3h_entity_resolution_audit_normalized_ticker
  ON public.tier3h_entity_resolution_audit (normalized_ticker);
CREATE INDEX IF NOT EXISTS idx_tier3h_entity_resolution_audit_duplicate_group_key
  ON public.tier3h_entity_resolution_audit (duplicate_group_key);
