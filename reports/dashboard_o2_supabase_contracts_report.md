# Dashboard O2 Supabase Contracts Report

## Objective
Define a deterministic, contract-only mapping from Dashboard O1 payload groups to Supabase persistence table batches.

## Scope
- Deterministic table contracts.
- Deterministic unique-key and column contracts.
- Deterministic payload validation.
- Deterministic upsert-batch envelope construction.
- Deterministic persistence manifest and checksum generation.

## Non-goals
- No database writes.
- No network calls.
- No file-write behavior in module APIs.
- No Streamlit UI creation.
- No new scoring or intelligence logic.

## Table mapping inventory
- `dashboard_entity_facts` -> `expectation_failure_dashboard_entity_facts`
- `dashboard_subsector_facts` -> `expectation_failure_dashboard_subsector_facts`
- `dashboard_alert_facts` -> `expectation_failure_dashboard_alert_facts`
- `dashboard_replay_facts` -> `expectation_failure_dashboard_replay_facts`
- `dashboard_benchmark_facts` -> `expectation_failure_dashboard_benchmark_facts`
- `dashboard_evidence_facts` -> `expectation_failure_dashboard_evidence_facts`
- `dashboard_report_metadata` -> `expectation_failure_dashboard_report_metadata`
- `dashboard_export_manifest` -> `expectation_failure_dashboard_export_manifest`

## Unique key inventory
- Entity facts: `run_id`, `entity_id`
- Subsector facts: `run_id`, `subsector`
- Alert facts: `run_id`, `entity_id`, `alert_state`
- Replay facts: `run_id`, `replay_date_sgt`, `entity_id`, `replay_sequence`
- Benchmark facts: `run_id`, `entity_id`, `benchmark_id`
- Evidence facts: `run_id`, `entity_id`, `evidence_id`
- Report metadata: `run_id`, `report_id`
- Export manifest: `run_id`, `checksum`

## Validation behavior
Validation enforces payload-group presence, accepted row container types, flat row shape, required and unique-key columns, duplicate unique-key rejection, forbidden-language exclusion, and deterministic table ordering checks.

## Deterministic guarantees
- Fixed table ordering.
- Fixed key ordering in API outputs.
- Stable sorting within each upsert batch by deterministic sort key.
- Stable manifest checksum from canonical JSON serialization.

## Supabase readiness assessment
The output is ready for downstream persistence orchestration as a deterministic `upsert_contract_only` envelope, with no runtime-side effects.

## Implementation boundaries
Module scope is contract and validation only, preserving immutable input safety and excluding persistence or UI execution paths.

## Next recommended phase
Dashboard O3 can integrate execution orchestration that consumes O2 contracts for actual Supabase write flows, with RLS-safe persistence adapters and runtime telemetry.
