# Supabase Table Contract Template

_Last updated: 2026-05-14_

Copy this template for every important Supabase table used by production, replay, propagation, telemetry, or dashboards.

---

## `<table_name>`

### Summary

| Field | Value |
|---|---|
| Contract status | Draft / Active / Legacy / Deprecated / Retired |
| Business purpose |  |
| Runtime layer | n8n / GitHub Actions / Python / Supabase / Streamlit |
| Primary producer |  |
| Secondary producers |  |
| Primary consumers |  |
| Owner |  |
| Last reviewed |  |

### Production contract

| Field | Value |
|---|---|
| Write mode | insert / upsert / delete-insert / append-only |
| Primary key / unique key |  |
| Expected write frequency |  |
| Expected row volume |  |
| Freshness SLA |  |
| Retention policy |  |
| Backfill supported | yes / no / partial |
| Replay-safe | yes / no / unknown |

### Required columns

| Column | Type | Required | Source | Notes |
|---|---|---|---|---|
| `run_id` | text | Recommended | workflow / Python entrypoint | Enables lineage tracking |
| `run_date_sgt` | date | Recommended | workflow / SQL default | Singapore business date |
| `created_at` | timestamptz | Recommended | database default | Insert timestamp |
| `updated_at` | timestamptz | Optional | database trigger/app | Update timestamp |

### Data quality expectations

| Check | Expected behavior |
|---|---|
| Non-null key fields |  |
| Duplicate policy |  |
| Date range policy |  |
| Numeric range policy |  |
| Empty batch handling |  |
| Partial batch handling |  |

### Dependency map

| Direction | Workflow/script/table | Notes |
|---|---|---|
| Upstream |  |  |
| Downstream |  |  |
| Dashboard |  |  |
| Alerting |  |  |

### RLS and access policy

| Access path | Expected permission |
|---|---|
| GitHub Actions service role | write where required |
| n8n credentials | write only required tables |
| Streamlit anon/publishable key | read-only where possible |
| Local development | restricted, no production secrets in repo |

### Migration notes

- Additive changes preferred.
- Breaking changes require compatibility view or dual-write period.
- Update dependent Streamlit dashboards and validation gates before removing columns.

### Open questions

- 
