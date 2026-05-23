# D2 Dashboard Supabase Schema Report

## Objective
Implement deterministic Supabase migration and schema contract for dashboard operationalization outputs.

## Scope
- Static SQL migration for O6/O7/O8-aligned dashboard tables.
- Deterministic Python schema contract and certification helpers.
- Contract validation tests.

## Non-goals
- No live database writes.
- No Supabase client creation.
- No environment variable access.
- No network/LLM/market data calls.

## Relationship to O6/O7/O8/O9
- O6 supplies finding/export record semantics.
- O7 supplies persistence adapter expectations.
- O8 supplies readback verification coverage.
- O9 closeout inherits certified schema readiness.

## Table inventory
- dashboard_finding_records
- dashboard_narrative_records
- dashboard_evidence_map_records
- dashboard_supervisor_panel_records
- dashboard_export_manifests
- dashboard_governance_records
- dashboard_replay_metadata_records
- dashboard_persistence_audit_records

## Column contract
Each table includes deterministic common fields (`record_id`, `record_type`, checksums, timestamps, JSONB payload/lineage/evidence/governance/replay fields) plus table-specific business columns.

## Index and constraint methodology
- B-tree indexes on `record_type`, `source_payload_checksum`, `export_checksum` across all tables.
- GIN indexes on `payload`, `lineage_refs`, and `evidence_refs` across all tables.
- Domain indexes for finding, narrative, and audit lookup fields.
- Primary key on `record_id` for all tables.

## RLS stance
RLS is intentionally not enabled in migration; policy selection remains an explicit deployment-stage decision.

## Certification states
- `CERTIFIED_DASHBOARD_SCHEMA_READY`
- `DEGRADED_DASHBOARD_SCHEMA_READY`
- `BLOCKED_DASHBOARD_SCHEMA_INVALID`

## Governance boundaries
Certification validates required inventory/columns/indexes/constraints and prevents forbidden live-execution behavior patterns.

## Deployment guidance
Apply migration via existing Supabase migration workflow and run D2 tests before promotion.

## Final supervisor closeout status
`CERTIFIED_DASHBOARD_SCHEMA_READY` (when full contract and migration are present).
