# Dashboard Contract Alignment Finalization Report

## Observed Insert Failures
- NOT NULL violations on `run_date_sgt` across entity, subsector, alert, benchmark, evidence, certification, and run-manifest table writes.
- Replay write failure from sending string replay identifier into integer `replay_sequence`.
- Certification report upsert failure from `ON CONFLICT (run_id, report_id)` without matching unique/exclusion constraint.

## Final Alignment Decisions
1. **Canonical date contract:** preserve existing deployed `run_date_sgt` contract and include deterministic `run_date_sgt = "2026-01-01"` in D1 payload rows that require it.
2. **Replay contract:** keep ordered replay slot as integer (`replay_sequence=1`) and preserve textual replay identifier separately as `replay_batch_id`.
3. **Certification upsert contract:** keep O3 `ON CONFLICT run_id,report_id` and add matching deterministic unique index.

## Additive Migration Strategy
- Added `supabase/migrations/20260523_dashboard_contract_alignment_finalization.sql`.
- Additive-only operations:
  - `ADD COLUMN IF NOT EXISTS replay_batch_id TEXT` on `dashboard_replay_facts`.
  - `CREATE UNIQUE INDEX IF NOT EXISTS` on `dashboard_certification_reports (run_id, report_id)`.
- No drops, truncates, table recreation, or destructive rewrites.

## Deterministic Guarantees
- No `datetime.now()` or runtime timestamps added.
- Fixed `run_date_sgt` contract anchored to `2026-01-01`.
- Repeated payload generation remains stable.

## Expected Post-Fix Behavior
- D1 controlled write payloads satisfy NOT NULL `run_date_sgt` requirements.
- Replay rows satisfy integer `replay_sequence` type requirements while retaining stable replay batch identifier semantics.
- Certification report upserts resolve against concrete unique index and no longer fail with ON CONFLICT mismatch.

## Decision
`APPROVED_FOR_DASHBOARD_CONTRACT_ALIGNMENT_FINALIZATION`
