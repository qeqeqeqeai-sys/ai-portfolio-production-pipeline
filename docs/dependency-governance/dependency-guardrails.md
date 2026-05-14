# Dependency Guardrails

_Last updated: 2026-05-14_

## Purpose

This document defines guardrails for workflows that depend on other workflows, table freshness, schema contracts, or cron-offset sequencing.

The goal is to reduce race conditions, stale reads, duplicate writes, and silent downstream breakages.

## Current risk pattern

The repository currently relies heavily on:

- cron offsets between GitHub Actions workflows,
- n8n workflows writing shared Supabase tables,
- downstream Python jobs reading tables produced by earlier workflows,
- Streamlit dashboards assuming stable table contracts.

This is operationally workable, but hidden dependencies become riskier as the system grows.

## Dependency classes

| Dependency class | Example | Risk |
|---|---|---|
| Time-based dependency | Workflow B starts 10 minutes after Workflow A | Race condition if A runs long |
| Table freshness dependency | Phase 5B reads Phase 5A outputs | Stale or partial reads |
| Schema dependency | Dashboard expects column added by phase engine | Runtime or silent display errors |
| Replay dependency | Backfill job depends on checkpoint state | Duplicate or skipped windows |
| Telemetry dependency | Incident response depends on metrics table | Weak triage if metrics are missing |

## Required dependency documentation

Every production or phase workflow should document:

1. Upstream workflows.
2. Upstream tables.
3. Downstream workflows.
4. Downstream tables.
5. Freshness expectations.
6. Whether partial input is allowed.
7. Whether replay/backfill may write the same table.
8. Recovery behavior after failure.

## Minimum pre-run checks

For any workflow that reads upstream tables:

- Confirm upstream table has rows for expected `run_date_sgt`.
- Confirm upstream table was updated within expected freshness window.
- Confirm row count is above expected minimum.
- Confirm required columns exist.
- Confirm upstream run status is `success` where lineage tracking exists.

## Recommended workflow statuses

| Status | Meaning |
|---|---|
| `started` | Workflow/phase began execution |
| `dependency_check_failed` | Required upstream dependency missing or stale |
| `running` | Main computation is in progress |
| `success` | Outputs written and validated |
| `partial_success` | Some outputs written; downstream should handle carefully |
| `failed` | No reliable output should be consumed |
| `skipped` | Intentionally skipped due to no eligible input |

## Guardrail policy

### Production workflows

Production workflows should fail fast when required upstream inputs are missing or stale.

### Research workflows

Research workflows may proceed with warnings, but must not overwrite production outputs unless explicitly designed to do so.

### Replay/backfill workflows

Replay/backfill workflows should write with explicit `run_id`, date range, and checkpoint metadata.

### Dashboards

Dashboards should show missing/stale warnings instead of silently displaying old data.

## High-priority guardrails to add later

1. Run lineage table.
2. Dependency freshness view.
3. Standardized pre-run dependency check helper.
4. Dashboard freshness indicators.
5. Cross-layer schema contract checks.
