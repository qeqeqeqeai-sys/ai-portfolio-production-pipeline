# Table Contract Registry

_Last updated: 2026-05-14_

## Purpose

This registry documents the expected producer, consumer, freshness, and schema contract for important Supabase tables used by the modular structural transmission research platform.

This is a governance artifact only. It does not change runtime behavior.

## Contract principles

1. Every important table should have a named producer.
2. Every table consumed by downstream workflows should have a freshness expectation.
3. Dashboards should read from documented output or telemetry tables only.
4. Schema changes should be additive unless a migration plan exists.
5. Tables used by more than one runtime layer require stronger contract discipline.

## Contract status levels

| Status | Meaning |
|---|---|
| Draft | Known table class, contract not fully confirmed |
| Active | Used by current production or phase workflows |
| Legacy | Retained for compatibility or historical reference |
| Deprecated | Should not be used by new workflows |
| Retired | No longer used; retained only for audit/reference |

## Table classes

| Table class | Example tables | Primary producer | Primary consumers | Freshness expectation | Contract status |
|---|---|---|---|---|---|
| Raw fundamentals | `raw_fundamental_*`, factor input tables | n8n/FMP ingestion | n8n merge, Python scoring | Daily on market days | Draft |
| Raw prices | `raw_price_*`, EOD price tables | n8n/FMP ingestion | n8n merge, reversal scoring, dashboards | Daily on market days | Draft |
| Raw news / hype inputs | `raw_news_*`, hype input tables | n8n news workflows | hype scoring, AI transmission scoring | Daily or intraday depending workflow | Draft |
| Macro support | macro, stress, commodity support tables | n8n support workflows | risk layers, dashboards, alerts | Daily/weekly depending source | Draft |
| AI scores | `ai_transmission_scores`, `ai_stock_scores`, related score tables | Python AI transmission / n8n scoring | validation, Streamlit, alerts | Daily | Active |
| Explainability | explainability and attribution tables | Python explainability layer | Streamlit, diagnostics | Same day as score run | Active |
| Historical reconstruction | reconstruction and backfill output tables | Python historical reconstruction | validation, historical dashboards | Manual/backfill run dependent | Active |
| Graph nodes/edges | structural graph node/edge tables | graph foundation engines | propagation phases, dashboards | Daily after graph evolution | Active |
| Propagation outputs | phase4/phase5 propagation output tables | Python propagation engines | corridor, regime, forecasting, Streamlit | Daily after upstream graph run | Active |
| Corridor/regime outputs | corridor and regime forecast tables | Phase 5B/5C/5D engines | dashboards, research review | Daily after Phase 5D | Active |
| Telemetry | pipeline metrics, failure metrics, phase telemetry | scripts and phase engines | ops dashboards, incident response | Per run | Active |
| Checkpoints | replay/backfill checkpoints | replay/backfill engines | replay continuation, audit | Per replay/backfill run | Active |

## Minimum table contract template

Use this template when documenting each important table.

```markdown
## `<table_name>`

| Field | Value |
|---|---|
| Contract status | Draft / Active / Legacy / Deprecated / Retired |
| Primary producer |  |
| Secondary producers |  |
| Primary consumers |  |
| Runtime layer | n8n / GitHub Actions / Python / Supabase / Streamlit |
| Write frequency |  |
| Freshness expectation |  |
| Retention expectation |  |
| RLS expectation |  |
| Backfill behavior |  |
| Owner |  |

### Required columns

| Column | Type | Required | Notes |
|---|---|---|---|
| `run_date_sgt` | date | Recommended | Singapore business date |
| `run_id` | text | Recommended | Required for lineage-aware tables |
| `created_at` | timestamptz | Recommended | Insert timestamp |
| `updated_at` | timestamptz | Optional | Update timestamp |

### Contract checks

- [ ] Producer documented
- [ ] Consumers documented
- [ ] Freshness expectation documented
- [ ] Required columns listed
- [ ] Backfill behavior documented
- [ ] Dashboard dependency documented
```

## Immediate documentation priorities

1. AI transmission score tables.
2. Structural graph node/edge tables.
3. Phase 4/5 propagation output tables.
4. Telemetry and failure metric tables.
5. Historical replay/backfill checkpoint tables.

## Change policy

Before changing a contracted table:

1. Identify all producers and consumers.
2. Confirm whether the change is additive or breaking.
3. Add SQL migration file under `database/migrations/`.
4. Update this registry and relevant runbooks.
5. Validate dashboards and downstream workflows.
