# Dependency Freshness Checks

_Last updated: 2026-05-14_

## Purpose

Freshness checks prevent downstream workflows from reading stale, partial, or missing upstream data.

## Freshness dimensions

| Dimension | Meaning |
|---|---|
| Date freshness | Is there data for expected `run_date_sgt`? |
| Update freshness | Was the table updated recently enough? |
| Row-count freshness | Is the row count within expected range? |
| Lineage freshness | Did the upstream run finish successfully? |
| Schema freshness | Do required columns still exist? |

## Recommended freshness tiers

| Tier | Example | Suggested policy |
|---|---|---|
| Critical | Daily production scoring inputs | Fail if stale |
| High | Propagation/corridor inputs | Fail or skip with explicit status |
| Medium | Dashboard-only derived outputs | Warn if stale |
| Low | Research/backfill outputs | Warn and document |

## Freshness check template

```markdown
## Freshness check: `<dependency_name>`

| Field | Value |
|---|---|
| Upstream table |  |
| Downstream workflow |  |
| Expected date field | `run_date_sgt` |
| Maximum acceptable age |  |
| Minimum row count |  |
| Required upstream status | `success` |
| Failure behavior | fail / skip / warn |
| Owner |  |
```

## Critical checks to add first

1. Phase 5B should confirm Phase 5A/two-hop outputs are fresh.
2. Phase 5C should confirm Phase 5B corridor outputs are fresh.
3. Phase 5D should confirm Phase 5C regime dynamics outputs are fresh.
4. AI transmission validation should confirm daily scoring outputs are fresh.
5. Streamlit dashboards should show freshness warnings for stale outputs.

## Future implementation notes

Freshness checks can be implemented through:

- SQL views,
- Python pre-run helpers,
- GitHub Actions preflight steps,
- Streamlit warning banners,
- n8n validation nodes.

Recommended long-term direction:

```text
workflow starts
  -> dependency freshness checks
     -> fail/skip/warn
        -> main compute
           -> lineage + telemetry update
```
