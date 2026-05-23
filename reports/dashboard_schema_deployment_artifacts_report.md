# Dashboard Schema Deployment Artifacts Report

## Diagnostic Finding
Runtime diagnostics indicate Supabase client resolution is healthy, but read-path health is degraded due to schema mismatch (`PGRST205` missing-table responses).

## Missing Tables
- `public.dashboard_entity_facts`
- `public.dashboard_subsector_facts`
- `public.dashboard_alert_facts`
- `public.dashboard_replay_facts`
- `public.dashboard_benchmark_facts`
- `public.dashboard_evidence_facts`
- `public.dashboard_certification_reports`
- `public.dashboard_run_manifests`

## Schema Deployment Scope
This phase delivers additive-only schema/deployment support artifacts for the certified O4/O6 read path. No changes to intelligence logic, scoring, dashboard behavior, or write-path scope.

## Table Inventory
Canonical table inventory is defined by deterministic helper APIs and aligned to O6 read inventory:
- `dashboard_entity_facts`
- `dashboard_subsector_facts`
- `dashboard_alert_facts`
- `dashboard_replay_facts`
- `dashboard_benchmark_facts`
- `dashboard_evidence_facts`
- `dashboard_certification_reports`
- `dashboard_run_manifests`

## Column Inventory
Canonical columns are defined deterministically in `dashboard_schema_verification.py` and encoded in SQL migration DDL for each table.

## RLS / Read Policy Guidance
Migration includes:
- `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` for each dashboard table.
- `SELECT`-only read policies for `anon` and `authenticated` roles.
- No write policies included.

## Safety Boundaries
- Additive-only DDL.
- No `DROP TABLE`.
- No `DELETE` / `TRUNCATE`.
- No broad write policy grants.
- Read-only dashboard boundary preserved.

## Validation Performed
- Deterministic schema helper APIs added.
- SQL artifact table/column/index/constraint presence validated by tests.
- Safety checks validate absence of destructive statements and broad write policies.

## Final Decision
**APPROVED_FOR_DASHBOARD_SCHEMA_DEPLOYMENT_ARTIFACTS**
