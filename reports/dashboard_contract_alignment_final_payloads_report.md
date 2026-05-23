# Dashboard Contract Alignment Final Payloads Report

## Observed Final NOT NULL Failures
Final seed execution reached correct `dashboard_*` tables and insert execution, but failed on missing required fields:
- `dashboard_entity_facts.ticker`
- `dashboard_subsector_facts.entity_count`
- `dashboard_alert_facts.ticker`
- `dashboard_replay_facts.ticker`
- `dashboard_benchmark_facts.ticker`
- `dashboard_evidence_facts.ticker`
- `dashboard_certification_reports.certification_status`
- `dashboard_run_manifests.schema_version`

## Payload Alignment Changes
Deterministic D1 payload generation was extended to include the required NOT NULL fields without weakening constraints:
- Added deterministic `ticker` values in all affected fact payload rows.
- Added deterministic bounded `entity_count` integer in subsector payload rows.
- Added deterministic bounded `certification_status` label in certification report payload rows.
- Added fixed `schema_version` literal in run manifest payload rows.

## Deterministic Value Strategy
- No random generation.
- No `datetime.now()`.
- No UUID generation.
- Existing deterministic identifiers preserved (`run_id`, `replay_batch_id`, fixed timestamps).
- Existing checksum contract preserved and replayable through deterministic payload construction.

## Replayability and Contract Guarantees
- Canonical payload inventory remains stable across repeated generation.
- O3 write-path behavior remains unchanged; only D1 payload completeness was aligned.
- Schema strictness retained (no NOT NULL weakening, no destructive migration).

## Expected Final Seed Behavior
- D1 sample seed payload now satisfies deployed NOT NULL payload/schema contract.
- Write execution is expected to proceed without the listed missing-field violations.

## Decision
`APPROVED_FOR_FINAL_D1_PAYLOAD_ALIGNMENT`
