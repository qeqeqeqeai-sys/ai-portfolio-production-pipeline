# D8.B2-R Replay Candidate Source Repair & Supabase Client Resolution Audit

## Objective
Audit and repair read-only D8.B2 replay candidate source resolution before any non-dry-run execution.

## Trigger Condition
Observed dry-run status included `client_resolved=false`, `replay rows loaded=0`, `manifest rows loaded=0`, and `candidate count=0`.

## Audited Client Paths
- D7 client resolution path uses `resolve_streamlit_supabase_client` from O7 runtime.
- D8.B2 previously had no equivalent read-path client resolution audit surface.
- D8.B2-R now reuses D7/O7 compatible resolution diagnostics.

## Audited Replay Candidate Sources
- `dashboard_replay_metadata_records`
- `dashboard_export_manifests`
- D7-derived historical run construction (`build_d7_historical_runs_from_integrity`)

## Root Cause Found
Primary root cause is **missing D8.B2 source diagnostics and client-resolution parity surface** with D7, causing unresolved client state and empty source ambiguity to be collapsed into generic no-candidate outcomes.

## Source Inventory Summary
D8.B2-R now reports:
- client resolution status
- credential presence flags (no secret exposure)
- expected vs accessible tables
- replay/manifest row counts
- historical derivation counts
- candidate derivation counts
- rejected derivation IDs for missing required fields

## Table/Source Shape Findings
Candidate adapter requires:
- run_id
- run_timestamp
- payload_checksum
- source_trace
- payload_reference

Rows missing required fields are rejected deterministically.

## Repair Made
- Added read-only diagnostic module with status taxonomy.
- Added deterministic history-row-to-candidate adapter.
- Added D8.B2 dry-run integration helper returning source readiness/block statuses.

## Remaining Limitations
- Final readiness still depends on runtime credentials and actual table accessibility in environment.

## Recommendation
- `READY_FOR_D8_B2_DRY_RUN_RETRY` when source status = `SOURCE_READY`
- else blocked status per diagnostics.

## Deterministic Guarantees
- Read-only querying only.
- No writes/updates/deletes/upserts.
- Stable ordered candidate derivation.
- No synthetic candidate fabrication.

## Governance Confirmation
D8.B2-R module and tests enforce read-only/no-fabrication boundaries.

## Tests Run / Results
See pytest command outputs in operator run log.
