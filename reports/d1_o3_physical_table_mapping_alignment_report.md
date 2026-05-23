# D1 O3 Physical Table Mapping Alignment Report

## Observed Failure
D1 seed execution used correct planned payload groups (`dashboard_*`) but O3 write result statuses showed failed writes to legacy-prefixed physical tables (`expectation_failure_dashboard_*`).

## Root Cause
`TABLE_CONFIG` in `dashboard_o2_supabase_contracts.py` mapped canonical payload keys to legacy `expectation_failure_dashboard_*` physical `table_name` values.
O3 consumes O2 contracts directly, so controlled writes targeted non-deployed table names.

## Old Wrong Physical Table Names
- expectation_failure_dashboard_entity_facts
- expectation_failure_dashboard_subsector_facts
- expectation_failure_dashboard_alert_facts
- expectation_failure_dashboard_replay_facts
- expectation_failure_dashboard_benchmark_facts
- expectation_failure_dashboard_evidence_facts
- expectation_failure_dashboard_certification_reports
- expectation_failure_dashboard_run_manifests

## New Canonical Physical Table Names
- dashboard_entity_facts
- dashboard_subsector_facts
- dashboard_alert_facts
- dashboard_replay_facts
- dashboard_benchmark_facts
- dashboard_evidence_facts
- dashboard_certification_reports
- dashboard_run_manifests

## Safety Boundary
- O3 controlled write path preserved (contract-driven write plan + injected client only).
- No raw SQL introduced.
- No uncontrolled writes added.
- Verify-readback remains available.

## Expected Post-Fix Workflow Output
- `planned_table_row_counts` shows canonical `dashboard_*` tables.
- `write_result_statuses` table names match canonical `dashboard_*` tables.
- `--execute --verify-readback` exits non-zero when any write_result_status is `failed` or readback is not `verified_non_empty`.

## Decision
**APPROVED_FOR_D1_O3_PHYSICAL_TABLE_MAPPING_ALIGNMENT_FIX**
