# Schema Change Policy

_Last updated: 2026-05-14_

## Purpose

This policy defines how Supabase schema changes should be introduced without breaking n8n workflows, Python engines, GitHub Actions, or Streamlit dashboards.

## Guiding principles

1. Prefer additive schema changes.
2. Avoid dropping or renaming columns used by active workflows.
3. Use compatibility views when changing table shape.
4. Document producers and consumers before making breaking changes.
5. Treat dashboard dependencies as production dependencies.

## Change categories

| Category | Example | Risk | Required action |
|---|---|---|---|
| Additive | Add nullable column | Low | Migration + registry update |
| Additive with default | Add non-null column with default | Medium | Migration + validation |
| Rename | Rename column/table | High | Compatibility view or dual-write |
| Type change | numeric to text | High | Migration plan + downstream testing |
| Drop | Remove table/column | Critical | Deprecation period + approval |
| Constraint change | Add unique key | Medium/High | Backfill/dedup before migration |

## Required checklist before schema changes

- [ ] Identify producers.
- [ ] Identify consumers.
- [ ] Check GitHub Actions references.
- [ ] Check n8n workflow references.
- [ ] Check Python imports/queries.
- [ ] Check Streamlit dashboards.
- [ ] Check replay/backfill behavior.
- [ ] Add migration SQL under `database/migrations/`.
- [ ] Update table contract registry.
- [ ] Confirm rollback approach.

## Compatibility approach

For breaking changes, use one of:

1. Dual-write old and new columns/tables.
2. Create compatibility view with old shape.
3. Add new table and migrate consumers gradually.
4. Keep old table as legacy until consumers are migrated.

## Naming convention for migrations

```text
YYYYMMDDHHMM_<domain>_<change>.sql
```

Example:

```text
202605141030_graph_add_corridor_index.sql
```
