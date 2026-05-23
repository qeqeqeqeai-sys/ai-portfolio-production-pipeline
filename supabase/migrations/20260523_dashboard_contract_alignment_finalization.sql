BEGIN;

ALTER TABLE IF EXISTS public.dashboard_replay_facts
    ADD COLUMN IF NOT EXISTS replay_batch_id TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_dashboard_certification_reports_run_id_report_id_unique
    ON public.dashboard_certification_reports (run_id, report_id);

COMMIT;
