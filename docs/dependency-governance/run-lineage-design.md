# Run Lineage Design

_Last updated: 2026-05-14_

## Purpose

Run lineage records how workflows, phases, tables, and output batches relate to each other.

This creates an audit trail across:

- GitHub Actions,
- n8n workflows,
- Python engines,
- Supabase output tables,
- replay/backfill jobs,
- telemetry writers.

## Why this matters

The system currently has several implicit dependencies based on cron timing and shared table state. A lineage layer helps answer:

- Which workflow produced this table output?
- Did the upstream workflow finish successfully?
- Was this output produced from fresh inputs?
- Which downstream workflows consumed this run?
- Was this output from production, research, or backfill mode?

## Recommended table: `pipeline_run_lineage`

Minimum fields:

| Column | Purpose |
|---|---|
| `id` | Surrogate primary key |
| `run_id` | Unique run identifier for workflow/phase execution |
| `parent_run_id` | Optional upstream run ID |
| `workflow_name` | GitHub Actions or n8n workflow name |
| `phase` | Logical phase, e.g. `phase5b_corridor_intelligence` |
| `runtime_layer` | `github_actions`, `n8n`, `python`, `manual`, `streamlit` |
| `run_mode` | `production`, `research`, `backfill`, `replay`, `manual` |
| `status` | Run status |
| `run_date_sgt` | Singapore business date |
| `started_at` | Start timestamp |
| `completed_at` | Completion timestamp |
| `source_tables` | JSON list of input tables |
| `tables_written` | JSON list of output tables |
| `row_counts` | JSON map of table to row count |
| `dependency_status` | Summary dependency status |
| `error_class` | Normalized error class if failed |
| `error_message` | Sanitized error message |
| `metadata` | Additional runtime metadata |
| `created_at` | Insert timestamp |

## Recommended usage pattern

1. Insert lineage record at workflow start with status `started`.
2. Run dependency checks.
3. Update status to `running`.
4. Execute workflow/phase.
5. Record output tables and row counts.
6. Update status to `success`, `partial_success`, or `failed`.
7. Dashboards and downstream checks read lineage before trusting outputs.

## Run ID format

Recommended format:

```text
<workflow_or_phase>__<YYYYMMDD>__<HHMMSS>__<short_random_suffix>
```

Example:

```text
phase5b_corridor__20260514__233500__a7f3
```

## Relationship to telemetry

Lineage is not a replacement for telemetry.

| Layer | Purpose |
|---|---|
| Lineage | What ran, what it depended on, what it wrote |
| Telemetry | How well it ran, row counts, latency, errors, warnings |
| Incident runbook | What to do when something fails |

## Adoption strategy

Phase 1: create table and document expected fields.  
Phase 2: write lineage from new workflows only.  
Phase 3: backfill lineage for critical workflows.  
Phase 4: add dependency guards that read lineage before running downstream phases.
