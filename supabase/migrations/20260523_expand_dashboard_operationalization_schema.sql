BEGIN;

ALTER TABLE IF EXISTS public.dashboard_entity_facts
    ADD COLUMN IF NOT EXISTS valuation_stretch_score DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS fundamental_support_score DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS narrative_saturation_score DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS certainty_fragility_score DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS structural_weakness_score DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS relative_fragility_rank INTEGER,
    ADD COLUMN IF NOT EXISTS asymmetry_label TEXT,
    ADD COLUMN IF NOT EXISTS dominant_driver TEXT,
    ADD COLUMN IF NOT EXISTS expectation_failure_score DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS risk_label TEXT,
    ADD COLUMN IF NOT EXISTS as_of_sgt TEXT,
    ADD COLUMN IF NOT EXISTS sample_data_flag BOOLEAN;

ALTER TABLE IF EXISTS public.dashboard_subsector_facts
    ADD COLUMN IF NOT EXISTS max_composite_score DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS dominant_subsector_driver TEXT,
    ADD COLUMN IF NOT EXISTS cluster_label TEXT,
    ADD COLUMN IF NOT EXISTS subsector_id TEXT,
    ADD COLUMN IF NOT EXISTS subsector_score DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS risk_label TEXT,
    ADD COLUMN IF NOT EXISTS as_of_sgt TEXT,
    ADD COLUMN IF NOT EXISTS sample_data_flag BOOLEAN;

ALTER TABLE IF EXISTS public.dashboard_alert_facts
    ADD COLUMN IF NOT EXISTS deterioration_label TEXT,
    ADD COLUMN IF NOT EXISTS alert_explanation_template_id TEXT,
    ADD COLUMN IF NOT EXISTS severity TEXT,
    ADD COLUMN IF NOT EXISTS alert_score DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS as_of_sgt TEXT,
    ADD COLUMN IF NOT EXISTS sample_data_flag BOOLEAN;

ALTER TABLE IF EXISTS public.dashboard_replay_facts
    ADD COLUMN IF NOT EXISTS benchmark_relative_label TEXT,
    ADD COLUMN IF NOT EXISTS replay_score DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS as_of_sgt TEXT,
    ADD COLUMN IF NOT EXISTS sample_data_flag BOOLEAN;

ALTER TABLE IF EXISTS public.dashboard_benchmark_facts
    ADD COLUMN IF NOT EXISTS benchmark_score DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS benchmark_label TEXT,
    ADD COLUMN IF NOT EXISTS as_of_sgt TEXT,
    ADD COLUMN IF NOT EXISTS sample_data_flag BOOLEAN;

ALTER TABLE IF EXISTS public.dashboard_evidence_facts
    ADD COLUMN IF NOT EXISTS confidence_score DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS as_of_sgt TEXT,
    ADD COLUMN IF NOT EXISTS sample_data_flag BOOLEAN;

ALTER TABLE IF EXISTS public.dashboard_certification_reports
    ADD COLUMN IF NOT EXISTS report_id TEXT,
    ADD COLUMN IF NOT EXISTS certification_state TEXT,
    ADD COLUMN IF NOT EXISTS schema_version TEXT,
    ADD COLUMN IF NOT EXISTS module_version TEXT,
    ADD COLUMN IF NOT EXISTS entity_fact_count INTEGER,
    ADD COLUMN IF NOT EXISTS subsector_fact_count INTEGER,
    ADD COLUMN IF NOT EXISTS alert_fact_count INTEGER,
    ADD COLUMN IF NOT EXISTS replay_fact_count INTEGER,
    ADD COLUMN IF NOT EXISTS benchmark_fact_count INTEGER,
    ADD COLUMN IF NOT EXISTS evidence_fact_count INTEGER,
    ADD COLUMN IF NOT EXISTS generated_at_sgt TEXT,
    ADD COLUMN IF NOT EXISTS as_of_sgt TEXT,
    ADD COLUMN IF NOT EXISTS sample_data_flag BOOLEAN;

ALTER TABLE IF EXISTS public.dashboard_run_manifests
    ADD COLUMN IF NOT EXISTS export_groups JSONB,
    ADD COLUMN IF NOT EXISTS record_counts JSONB,
    ADD COLUMN IF NOT EXISTS deterministic_sort_keys JSONB,
    ADD COLUMN IF NOT EXISTS invariant_flags JSONB,
    ADD COLUMN IF NOT EXISTS sample_data_flag BOOLEAN;

CREATE INDEX IF NOT EXISTS idx_dashboard_entity_facts_as_of_sgt ON public.dashboard_entity_facts (as_of_sgt);
CREATE INDEX IF NOT EXISTS idx_dashboard_entity_facts_sample_data_flag ON public.dashboard_entity_facts (sample_data_flag);
CREATE INDEX IF NOT EXISTS idx_dashboard_alert_facts_alert_score ON public.dashboard_alert_facts (alert_score);
CREATE INDEX IF NOT EXISTS idx_dashboard_alert_facts_as_of_sgt ON public.dashboard_alert_facts (as_of_sgt);
CREATE INDEX IF NOT EXISTS idx_dashboard_run_manifests_sample_data_flag ON public.dashboard_run_manifests (sample_data_flag);

COMMIT;
