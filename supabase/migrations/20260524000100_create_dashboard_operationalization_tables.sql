-- D2 deterministic dashboard operationalization schema.

CREATE TABLE IF NOT EXISTS dashboard_finding_records (
  record_id text PRIMARY KEY,
  record_type text NOT NULL,
  source_payload_checksum text,
  export_checksum text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  lineage_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  governance_notes jsonb NOT NULL DEFAULT '[]'::jsonb,
  replay_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  finding_id text NOT NULL,
  finding_type text,
  finding_title text,
  finding_severity text,
  finding_direction text,
  confidence_label text
);

CREATE TABLE IF NOT EXISTS dashboard_narrative_records (
  record_id text PRIMARY KEY,
  record_type text NOT NULL,
  source_payload_checksum text,
  export_checksum text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  lineage_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  governance_notes jsonb NOT NULL DEFAULT '[]'::jsonb,
  replay_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  narrative_section text NOT NULL,
  related_finding_ids jsonb NOT NULL DEFAULT '[]'::jsonb
);

CREATE TABLE IF NOT EXISTS dashboard_evidence_map_records (
  record_id text PRIMARY KEY,
  record_type text NOT NULL,
  source_payload_checksum text,
  export_checksum text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  lineage_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  governance_notes jsonb NOT NULL DEFAULT '[]'::jsonb,
  replay_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  finding_id text,
  evidence_ref text
);

CREATE TABLE IF NOT EXISTS dashboard_supervisor_panel_records (
  record_id text PRIMARY KEY,
  record_type text NOT NULL,
  source_payload_checksum text,
  export_checksum text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  lineage_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  governance_notes jsonb NOT NULL DEFAULT '[]'::jsonb,
  replay_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  panel_name text,
  panel_status text
);

CREATE TABLE IF NOT EXISTS dashboard_export_manifests (
  record_id text PRIMARY KEY,
  record_type text NOT NULL,
  source_payload_checksum text,
  export_checksum text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  lineage_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  governance_notes jsonb NOT NULL DEFAULT '[]'::jsonb,
  replay_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  manifest_id text,
  manifest_checksum text
);

CREATE TABLE IF NOT EXISTS dashboard_governance_records (
  record_id text PRIMARY KEY,
  record_type text NOT NULL,
  source_payload_checksum text,
  export_checksum text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  lineage_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  governance_notes jsonb NOT NULL DEFAULT '[]'::jsonb,
  replay_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  governance_status text,
  forbidden_capabilities jsonb NOT NULL DEFAULT '[]'::jsonb
);

CREATE TABLE IF NOT EXISTS dashboard_replay_metadata_records (
  record_id text PRIMARY KEY,
  record_type text NOT NULL,
  source_payload_checksum text,
  export_checksum text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  lineage_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  governance_notes jsonb NOT NULL DEFAULT '[]'::jsonb,
  replay_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  replay_id text,
  replay_checksum text
);

CREATE TABLE IF NOT EXISTS dashboard_persistence_audit_records (
  record_id text PRIMARY KEY,
  record_type text NOT NULL,
  source_payload_checksum text,
  export_checksum text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  lineage_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
  governance_notes jsonb NOT NULL DEFAULT '[]'::jsonb,
  replay_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  audit_id text,
  batch_id text,
  target_table text,
  write_status text
);

-- Shared indexes.
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY[
    'dashboard_finding_records','dashboard_narrative_records','dashboard_evidence_map_records','dashboard_supervisor_panel_records',
    'dashboard_export_manifests','dashboard_governance_records','dashboard_replay_metadata_records','dashboard_persistence_audit_records']
  LOOP
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (record_type);', t || '_record_type_idx', t);
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (source_payload_checksum);', t || '_source_checksum_idx', t);
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (export_checksum);', t || '_export_checksum_idx', t);
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I USING GIN (payload);', t || '_payload_gin_idx', t);
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I USING GIN (lineage_refs);', t || '_lineage_refs_gin_idx', t);
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I USING GIN (evidence_refs);', t || '_evidence_refs_gin_idx', t);
  END LOOP;
END $$;

CREATE INDEX IF NOT EXISTS dashboard_finding_records_finding_id_idx ON dashboard_finding_records (finding_id);
CREATE INDEX IF NOT EXISTS dashboard_finding_records_finding_severity_idx ON dashboard_finding_records (finding_severity);
CREATE INDEX IF NOT EXISTS dashboard_finding_records_confidence_label_idx ON dashboard_finding_records (confidence_label);
CREATE INDEX IF NOT EXISTS dashboard_narrative_records_narrative_section_idx ON dashboard_narrative_records (narrative_section);
CREATE INDEX IF NOT EXISTS dashboard_persistence_audit_records_batch_id_idx ON dashboard_persistence_audit_records (batch_id);
CREATE INDEX IF NOT EXISTS dashboard_persistence_audit_records_target_table_idx ON dashboard_persistence_audit_records (target_table);
CREATE INDEX IF NOT EXISTS dashboard_persistence_audit_records_write_status_idx ON dashboard_persistence_audit_records (write_status);

-- RLS intentionally not enabled here; deployment policy remains an explicit environment decision.
