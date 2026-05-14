# Dependency Governance

_Last updated: 2026-05-14_

This folder contains Tier 2 governance artifacts for dependency visibility, freshness checks, lineage, and schema-change discipline.

## Files

| File | Purpose |
|---|---|
| `dependency-guardrails.md` | Operational rules for upstream/downstream dependencies |
| `run-lineage-design.md` | Design for `pipeline_run_lineage` and run tracking |
| `freshness-checks.md` | Freshness concepts and check templates |
| `schema-change-policy.md` | Policy for safe Supabase schema changes |

## Related folders

| Folder | Purpose |
|---|---|
| `docs/data-contracts/` | Table contract registry and templates |
| `database/migrations/` | SQL migrations |
| `database/views/` | SQL views for governance and observability |
| `database/functions/` | SQL helper functions |
