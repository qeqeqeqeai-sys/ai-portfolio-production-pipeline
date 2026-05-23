# Dashboard Full Schema Payload Alignment Report

## Iterative failure history

Recent D1 insert retries surfaced NOT NULL omissions incrementally (`alert_state`, `alert_entity_count`, `active_alert_flag`, `fragility_band`, `benchmark_fragility_score`, `normalized_score`). This pass replaces reactive failure-driven discovery with a complete canonical required-column alignment.

## Full-schema introspection alignment decision

**Final decision:** `APPROVED_FOR_FULL_DASHBOARD_SCHEMA_PAYLOAD_ALIGNMENT`

The D1 deterministic seed payload now performs a single comprehensive required-field population pass across all dashboard fact/report/manifest tables.

## Canonical required NOT NULL inventory

Derived from deployed dashboard schema migration (`database/migrations/20260523_create_dashboard_operationalization_tables.sql`):

- `dashboard_entity_facts`: `run_id`, `run_date_sgt`, `entity_id`, `entity_name`, `ticker`, `subsector`, `composite_score`, `relative_fragility_band`, `alert_state`, `benchmark_relative_label`, `evidence_quality_flag`, `certification_status`, `replay_checksum`
- `dashboard_subsector_facts`: `run_id`, `run_date_sgt`, `subsector`, `entity_count`, `avg_composite_score`, `fragile_entity_count`, `alert_entity_count`, `subsector_fragility_band`, `evidence_quality_summary`, `replay_checksum`
- `dashboard_alert_facts`: `run_id`, `run_date_sgt`, `entity_id`, `ticker`, `subsector`, `alert_state`, `alert_severity_band`, `active_alert_flag`, `dominant_alert_driver`, `evidence_quality_flag`, `replay_checksum`
- `dashboard_replay_facts`: `run_id`, `replay_date_sgt`, `entity_id`, `ticker`, `subsector`, `composite_score`, `fragility_band`, `alert_state`, `deterioration_label`, `replay_sequence`, `replay_checksum`
- `dashboard_benchmark_facts`: `run_id`, `run_date_sgt`, `entity_id`, `ticker`, `subsector`, `benchmark_id`, `entity_fragility_score`, `benchmark_fragility_score`, `relative_gap`, `relative_gap_band`, `benchmark_relative_label`, `outlier_flag`, `replay_checksum`
- `dashboard_evidence_facts`: `run_id`, `run_date_sgt`, `entity_id`, `ticker`, `evidence_id`, `evidence_type`, `source_metric`, `source_value`, `normalized_score`, `quality_flag`, `evidence_chain_position`, `template_id`, `replay_checksum`
- `dashboard_certification_reports`: `run_id`, `run_date_sgt`, `certification_status`, `report_type`, `export_manifest_checksum`
- `dashboard_run_manifests`: `run_id`, `checksum`, `run_date_sgt`, `schema_version`, `module_version`

## Deterministic enrichment strategy

- Deterministic literals for labels/states/checksums IDs.
- Deterministic bounded numerics (`0..100` scores, `0..1` normalized evidence values).
- Deterministic booleans and counts.
- Fixed replay-safe values (`FIXED_TIMESTAMP`, `FIXED_RUN_DATE_SGT`, stable manifest checksums).
- No randomization, no runtime time generation, no UUID generation.

## Expected final insert behavior

D1 payload generation now includes all currently required NOT NULL fields for all operational dashboard tables in one cycle, eliminating iterative failure discovery for required business columns.
