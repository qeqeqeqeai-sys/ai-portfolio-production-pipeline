# D1/O6 Dashboard Table Alignment Report

## Issue Observed
D1 controlled seeding completed successfully, but O6/O7 runtime diagnostics still reported empty dashboard read tables.

## Root Cause
D1/O2 write mapping used physical table names `dashboard_report_metadata` and `dashboard_export_manifest`, while O6/O7 read adapters expect `dashboard_certification_reports` and `dashboard_run_manifests`.

## Canonical Physical Table Inventory
- dashboard_entity_facts
- dashboard_subsector_facts
- dashboard_alert_facts
- dashboard_replay_facts
- dashboard_benchmark_facts
- dashboard_evidence_facts
- dashboard_certification_reports
- dashboard_run_manifests

## Changes Implemented
- Updated D1 seed payload keys to write certification rows to `dashboard_certification_reports`.
- Updated D1 seed payload keys to write manifest rows to `dashboard_run_manifests`.
- Updated D1 manifest table counts to report physical names.
- Updated O2 contract table mapping to align with canonical physical tables.
- Updated D1 runner table-count display to use O3 write plan physical table names.
- Added runner `--verify-readback` flag for read-only post-seed count verification using filtered `select(..., count='exact')`.
- Updated README demo seed instructions and canonical table list.

## Readback Verification Behavior
When `--verify-readback` is enabled, the runner prints row counts for canonical physical tables using read-only bounded select/count queries, with optional `run_id` filtering.

## Expected Post-fix Diagnostics
After controlled execution, O6/O7 diagnostics should no longer show empty tables caused by table-name mismatch; row presence now maps to canonical read tables.

## Decision
APPROVED_FOR_D1_O6_DASHBOARD_TABLE_ALIGNMENT_FIX
