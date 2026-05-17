ALTER TABLE IF EXISTS public.tier3h_entity_resolution_audit
  ADD COLUMN IF NOT EXISTS extracted_ticker text,
  ADD COLUMN IF NOT EXISTS raw_exchange text,
  ADD COLUMN IF NOT EXISTS security_type text,
  ADD COLUMN IF NOT EXISTS canonical_security_id text,
  ADD COLUMN IF NOT EXISTS identifier_source text,
  ADD COLUMN IF NOT EXISTS identifier_method text,
  ADD COLUMN IF NOT EXISTS identifier_confidence numeric,
  ADD COLUMN IF NOT EXISTS identifier_status text,
  ADD COLUMN IF NOT EXISTS identifier_explanation text,
  ADD COLUMN IF NOT EXISTS identifier_warnings jsonb NOT NULL DEFAULT '[]'::jsonb;

CREATE TABLE IF NOT EXISTS public.security_identifier_registry (
  canonical_security_id text PRIMARY KEY,
  ticker text NOT NULL,
  normalized_exchange text NOT NULL,
  security_type text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.security_alias_registry (
  alias text PRIMARY KEY,
  canonical_security_id text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.exchange_normalization_registry (
  raw_exchange text PRIMARY KEY,
  normalized_exchange text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
