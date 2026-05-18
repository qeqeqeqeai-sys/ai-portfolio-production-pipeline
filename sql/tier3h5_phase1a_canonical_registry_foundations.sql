-- Tier 3H.5 Phase 1A canonical registry foundations (deterministic / replayable)

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
  first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
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
  currency TEXT,
  source_record_hash TEXT NOT NULL,
  first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.tier3h5_registry_provenance (
  provenance_id TEXT PRIMARY KEY,
  ingestion_run_id TEXT NOT NULL,
  source_name TEXT NOT NULL,
  source_url TEXT,
  source_retrieved_at TIMESTAMPTZ NOT NULL,
  source_checksum TEXT NOT NULL,
  source_record_count INTEGER NOT NULL,
  accepted_record_count INTEGER NOT NULL,
  rejected_record_count INTEGER NOT NULL,
  duplicate_record_count INTEGER NOT NULL,
  conflict_record_count INTEGER NOT NULL,
  schema_version TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.tier3h5_registry_ingestion_runs (
  ingestion_run_id TEXT PRIMARY KEY,
  source_name TEXT NOT NULL,
  source_checksum TEXT NOT NULL,
  schema_version TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
