-- Dashboard operationalization schema deployment artifact (additive-only, deterministic).
-- Scope: create missing read tables for O4/O6 certified Streamlit dashboard path.

BEGIN;

CREATE TABLE IF NOT EXISTS public.dashboard_entity_facts (
    run_id TEXT NOT NULL,
    run_date_sgt TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    entity_name TEXT NOT NULL,
    ticker TEXT NOT NULL,
    subsector TEXT NOT NULL,
    composite_score DOUBLE PRECISION NOT NULL,
    relative_fragility_band TEXT NOT NULL,
    alert_state TEXT NOT NULL,
    benchmark_relative_label TEXT NOT NULL,
    evidence_quality_flag TEXT NOT NULL,
    certification_status TEXT NOT NULL,
    replay_checksum TEXT NOT NULL,
    PRIMARY KEY (run_id, entity_id)
);

CREATE TABLE IF NOT EXISTS public.dashboard_subsector_facts (
    run_id TEXT NOT NULL,
    run_date_sgt TEXT NOT NULL,
    subsector TEXT NOT NULL,
    entity_count INTEGER NOT NULL,
    avg_composite_score DOUBLE PRECISION NOT NULL,
    fragile_entity_count INTEGER NOT NULL,
    alert_entity_count INTEGER NOT NULL,
    subsector_fragility_band TEXT NOT NULL,
    evidence_quality_summary TEXT NOT NULL,
    replay_checksum TEXT NOT NULL,
    PRIMARY KEY (run_id, subsector)
);

CREATE TABLE IF NOT EXISTS public.dashboard_alert_facts (
    run_id TEXT NOT NULL,
    run_date_sgt TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    ticker TEXT NOT NULL,
    subsector TEXT NOT NULL,
    alert_state TEXT NOT NULL,
    alert_severity_band TEXT NOT NULL,
    active_alert_flag BOOLEAN NOT NULL,
    dominant_alert_driver TEXT NOT NULL,
    evidence_quality_flag TEXT NOT NULL,
    replay_checksum TEXT NOT NULL,
    PRIMARY KEY (run_id, entity_id, alert_state)
);

CREATE TABLE IF NOT EXISTS public.dashboard_replay_facts (
    run_id TEXT NOT NULL,
    replay_date_sgt TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    ticker TEXT NOT NULL,
    subsector TEXT NOT NULL,
    composite_score DOUBLE PRECISION NOT NULL,
    fragility_band TEXT NOT NULL,
    alert_state TEXT NOT NULL,
    deterioration_label TEXT NOT NULL,
    replay_sequence INTEGER NOT NULL,
    replay_checksum TEXT NOT NULL,
    PRIMARY KEY (run_id, replay_date_sgt, entity_id, replay_sequence)
);

CREATE TABLE IF NOT EXISTS public.dashboard_benchmark_facts (
    run_id TEXT NOT NULL,
    run_date_sgt TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    ticker TEXT NOT NULL,
    subsector TEXT NOT NULL,
    benchmark_id TEXT NOT NULL,
    entity_fragility_score DOUBLE PRECISION NOT NULL,
    benchmark_fragility_score DOUBLE PRECISION NOT NULL,
    relative_gap DOUBLE PRECISION NOT NULL,
    relative_gap_band TEXT NOT NULL,
    benchmark_relative_label TEXT NOT NULL,
    outlier_flag BOOLEAN NOT NULL,
    replay_checksum TEXT NOT NULL,
    PRIMARY KEY (run_id, entity_id, benchmark_id)
);

CREATE TABLE IF NOT EXISTS public.dashboard_evidence_facts (
    run_id TEXT NOT NULL,
    run_date_sgt TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    ticker TEXT NOT NULL,
    evidence_id TEXT NOT NULL,
    evidence_type TEXT NOT NULL,
    source_metric TEXT NOT NULL,
    source_value DOUBLE PRECISION NOT NULL,
    normalized_score DOUBLE PRECISION NOT NULL,
    quality_flag TEXT NOT NULL,
    evidence_chain_position INTEGER NOT NULL,
    template_id TEXT NOT NULL,
    replay_checksum TEXT NOT NULL,
    PRIMARY KEY (run_id, entity_id, evidence_id)
);

CREATE TABLE IF NOT EXISTS public.dashboard_certification_reports (
    run_id TEXT NOT NULL,
    run_date_sgt TEXT NOT NULL,
    certification_status TEXT NOT NULL,
    report_type TEXT NOT NULL,
    export_manifest_checksum TEXT NOT NULL,
    PRIMARY KEY (run_id, export_manifest_checksum)
);

CREATE TABLE IF NOT EXISTS public.dashboard_run_manifests (
    run_id TEXT NOT NULL,
    checksum TEXT NOT NULL,
    run_date_sgt TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    module_version TEXT NOT NULL,
    PRIMARY KEY (run_id, checksum)
);

CREATE INDEX IF NOT EXISTS idx_dashboard_entity_facts_run_id ON public.dashboard_entity_facts (run_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_entity_facts_run_date_sgt ON public.dashboard_entity_facts (run_date_sgt);
CREATE INDEX IF NOT EXISTS idx_dashboard_entity_facts_entity_id ON public.dashboard_entity_facts (entity_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_entity_facts_ticker ON public.dashboard_entity_facts (ticker);
CREATE INDEX IF NOT EXISTS idx_dashboard_entity_facts_subsector ON public.dashboard_entity_facts (subsector);

CREATE INDEX IF NOT EXISTS idx_dashboard_subsector_facts_run_id ON public.dashboard_subsector_facts (run_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_subsector_facts_run_date_sgt ON public.dashboard_subsector_facts (run_date_sgt);
CREATE INDEX IF NOT EXISTS idx_dashboard_subsector_facts_subsector ON public.dashboard_subsector_facts (subsector);

CREATE INDEX IF NOT EXISTS idx_dashboard_alert_facts_run_id ON public.dashboard_alert_facts (run_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_alert_facts_run_date_sgt ON public.dashboard_alert_facts (run_date_sgt);
CREATE INDEX IF NOT EXISTS idx_dashboard_alert_facts_entity_id ON public.dashboard_alert_facts (entity_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_alert_facts_ticker ON public.dashboard_alert_facts (ticker);
CREATE INDEX IF NOT EXISTS idx_dashboard_alert_facts_subsector ON public.dashboard_alert_facts (subsector);

CREATE INDEX IF NOT EXISTS idx_dashboard_replay_facts_run_id ON public.dashboard_replay_facts (run_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_replay_facts_replay_date_sgt ON public.dashboard_replay_facts (replay_date_sgt);
CREATE INDEX IF NOT EXISTS idx_dashboard_replay_facts_entity_id ON public.dashboard_replay_facts (entity_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_replay_facts_ticker ON public.dashboard_replay_facts (ticker);
CREATE INDEX IF NOT EXISTS idx_dashboard_replay_facts_subsector ON public.dashboard_replay_facts (subsector);

CREATE INDEX IF NOT EXISTS idx_dashboard_benchmark_facts_run_id ON public.dashboard_benchmark_facts (run_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_benchmark_facts_run_date_sgt ON public.dashboard_benchmark_facts (run_date_sgt);
CREATE INDEX IF NOT EXISTS idx_dashboard_benchmark_facts_entity_id ON public.dashboard_benchmark_facts (entity_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_benchmark_facts_ticker ON public.dashboard_benchmark_facts (ticker);
CREATE INDEX IF NOT EXISTS idx_dashboard_benchmark_facts_subsector ON public.dashboard_benchmark_facts (subsector);

CREATE INDEX IF NOT EXISTS idx_dashboard_evidence_facts_run_id ON public.dashboard_evidence_facts (run_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_evidence_facts_run_date_sgt ON public.dashboard_evidence_facts (run_date_sgt);
CREATE INDEX IF NOT EXISTS idx_dashboard_evidence_facts_entity_id ON public.dashboard_evidence_facts (entity_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_evidence_facts_ticker ON public.dashboard_evidence_facts (ticker);

CREATE INDEX IF NOT EXISTS idx_dashboard_certification_reports_run_id ON public.dashboard_certification_reports (run_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_certification_reports_run_date_sgt ON public.dashboard_certification_reports (run_date_sgt);

CREATE INDEX IF NOT EXISTS idx_dashboard_run_manifests_run_id ON public.dashboard_run_manifests (run_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_run_manifests_run_date_sgt ON public.dashboard_run_manifests (run_date_sgt);

-- Optional RLS/read policy guidance for Streamlit dashboard read path.
ALTER TABLE public.dashboard_entity_facts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dashboard_subsector_facts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dashboard_alert_facts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dashboard_replay_facts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dashboard_benchmark_facts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dashboard_evidence_facts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dashboard_certification_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dashboard_run_manifests ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'dashboard_entity_facts' AND policyname = 'dashboard_entity_facts_read_policy') THEN
        CREATE POLICY dashboard_entity_facts_read_policy ON public.dashboard_entity_facts FOR SELECT TO anon, authenticated USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'dashboard_subsector_facts' AND policyname = 'dashboard_subsector_facts_read_policy') THEN
        CREATE POLICY dashboard_subsector_facts_read_policy ON public.dashboard_subsector_facts FOR SELECT TO anon, authenticated USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'dashboard_alert_facts' AND policyname = 'dashboard_alert_facts_read_policy') THEN
        CREATE POLICY dashboard_alert_facts_read_policy ON public.dashboard_alert_facts FOR SELECT TO anon, authenticated USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'dashboard_replay_facts' AND policyname = 'dashboard_replay_facts_read_policy') THEN
        CREATE POLICY dashboard_replay_facts_read_policy ON public.dashboard_replay_facts FOR SELECT TO anon, authenticated USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'dashboard_benchmark_facts' AND policyname = 'dashboard_benchmark_facts_read_policy') THEN
        CREATE POLICY dashboard_benchmark_facts_read_policy ON public.dashboard_benchmark_facts FOR SELECT TO anon, authenticated USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'dashboard_evidence_facts' AND policyname = 'dashboard_evidence_facts_read_policy') THEN
        CREATE POLICY dashboard_evidence_facts_read_policy ON public.dashboard_evidence_facts FOR SELECT TO anon, authenticated USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'dashboard_certification_reports' AND policyname = 'dashboard_certification_reports_read_policy') THEN
        CREATE POLICY dashboard_certification_reports_read_policy ON public.dashboard_certification_reports FOR SELECT TO anon, authenticated USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'dashboard_run_manifests' AND policyname = 'dashboard_run_manifests_read_policy') THEN
        CREATE POLICY dashboard_run_manifests_read_policy ON public.dashboard_run_manifests FOR SELECT TO anon, authenticated USING (true);
    END IF;
END
$$;

COMMIT;
