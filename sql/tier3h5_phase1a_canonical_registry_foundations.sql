BEGIN;

CREATE TABLE IF NOT EXISTS public.tier3h5_registry_ingestion_runs (
  ingestion_run_id TEXT PRIMARY KEY,
  source_name TEXT NOT NULL,
  source_checksum TEXT NOT NULL,
  schema_version TEXT NOT NULL DEFAULT 'tier3h5_phase1a_v1',
  status TEXT NOT NULL DEFAULT 'started',
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.tier3h5_institutional_issuer_registry (
  issuer_id TEXT PRIMARY KEY,
  issuer_name_canonical TEXT NOT NULL,
  issuer_name_normalized TEXT NOT NULL,
  country_code TEXT,
  primary_exchange TEXT,
  primary_ticker TEXT,
  issuer_type TEXT,
  sec_cik TEXT,
  lei TEXT,
  issuer_status TEXT NOT NULL DEFAULT 'active',
  source_authority TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT tier3h5_issuer_sec_cik_key UNIQUE (sec_cik),
  CONSTRAINT tier3h5_issuer_lei_key UNIQUE (lei)
);

CREATE TABLE IF NOT EXISTS public.tier3h5_institutional_security_registry (
  security_id TEXT PRIMARY KEY,
  issuer_id TEXT NOT NULL REFERENCES public.tier3h5_institutional_issuer_registry(issuer_id),
  ticker TEXT NOT NULL,
  normalized_ticker TEXT NOT NULL,
  exchange TEXT NOT NULL,
  normalized_exchange TEXT NOT NULL,
  security_name TEXT,
  security_type TEXT NOT NULL,
  share_class TEXT,
  currency TEXT,
  listing_status TEXT NOT NULL DEFAULT 'active',
  is_primary_listing BOOLEAN NOT NULL DEFAULT FALSE,
  source_registry TEXT NOT NULL,
  source_record_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT tier3h5_security_deterministic_key UNIQUE (normalized_exchange, normalized_ticker, security_type, source_registry)
);

CREATE TABLE IF NOT EXISTS public.tier3h5_registry_provenance (
  provenance_id TEXT PRIMARY KEY,
  ingestion_run_id TEXT NOT NULL REFERENCES public.tier3h5_registry_ingestion_runs(ingestion_run_id),
  source_name TEXT NOT NULL,
  source_url TEXT,
  source_retrieved_at TIMESTAMPTZ NOT NULL,
  source_checksum TEXT NOT NULL,
  source_record_count INTEGER NOT NULL,
  accepted_record_count INTEGER NOT NULL,
  rejected_record_count INTEGER NOT NULL,
  duplicate_record_count INTEGER NOT NULL,
  conflict_record_count INTEGER NOT NULL,
  schema_version TEXT NOT NULL DEFAULT 'tier3h5_phase1a_v1',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_tier3h5_issuer_identity_unique
  ON public.tier3h5_institutional_issuer_registry(issuer_name_normalized, COALESCE(sec_cik, ''), COALESCE(lei, ''));

CREATE INDEX IF NOT EXISTS idx_tier3h5_security_issuer_id ON public.tier3h5_institutional_security_registry(issuer_id);
CREATE INDEX IF NOT EXISTS idx_tier3h5_provenance_ingestion_run_id ON public.tier3h5_registry_provenance(ingestion_run_id);

COMMIT;
