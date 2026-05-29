# DB-1 — Supabase Read Model for SEFI History

## Objective

Implement a deterministic, append-only Supabase read model for SEFI historical outputs so future review and retrieval can use compact relational rows instead of repeatedly loading token-heavy JSON artifacts.

## Schema Design

DB-1 adds registry, specialized, and generic fact tables under `supabase/migrations/20260529000100_create_sefi_history_read_model.sql`:

- `sefi_artifact_registry`
- `sefi_run_registry`
- `sefi_phase_runs`
- `sefi_hist_observations`
- `sefi_window_metrics`
- `sefi_sector_morphology`
- `sefi_symbol_metrics`
- `sefi_observation_facts`

Artifact path and SHA-256 are stored once in `sefi_artifact_registry`. Downstream read-model tables use `artifact_id` and `run_id` foreign keys rather than duplicating source path/checksum values. Each append-only table includes deterministic duplicate-prevention keys, timestamps, and bounded `payload_jsonb` metadata. `payload_jsonb` is capped at 8 KiB per row and is reserved for compact metadata only.

## Table Purpose

- `sefi_artifact_registry`: canonical source-artifact lineage, path, SHA-256, artifact kind, and schema version.
- `sefi_run_registry`: canonical run identity for a phase/artifact load.
- `sefi_phase_runs`: compact completed phase/run summary keyed to registry rows.
- `sefi_hist_observations`: bounded scalar observations extracted from completed SEFI/HIST summaries.
- `sefi_window_metrics`: normalized per-window metrics such as completeness, replay density, replay saturation, contradiction burden, HHI values, and symbol counts.
- `sefi_sector_morphology`: normalized sector/subsector/group morphology rows from cross-sectional and intra-group findings.
- `sefi_symbol_metrics`: normalized symbol-level rows when bounded weak-symbol observations are present.
- `sefi_observation_facts`: generic fact table with `phase_id`, `window_days`, `entity_type`, `entity_id`, `metric_name`, `metric_value`, `artifact_id`, and `run_id`, so future HIST-LONG phases can load metrics directly without report parsing.

## Loader Behavior

The loader module lives at `transmission_layers/history_read_model/loader.py` and reads only local JSON artifacts. It does not create a Supabase client, does not call FMP/provider APIs, and does not re-run any HIST-LONG phase. It computes source SHA-256 values, builds deterministic artifact/run identifiers, emits registry rows first, extracts normalized specialized rows, and emits generic observation facts from normalized metrics.

The runner at `scripts/run_db1_supabase_read_model_load.py` defaults to dry-run mode and reports row counts. It appends to Supabase only when explicitly invoked with `--execute` and externally provided credentials. Inserts are ordered so artifact/run registry rows precede dependent read-model rows.

## Query Helpers

Read-only helpers live at `transmission_layers/history_read_model/queries.py`:

- `get_phase_run_summary(phase_id)`
- `get_window_metrics(phase_id, window_days)`
- `get_sector_morphology(phase_id)`
- `get_symbol_metrics(phase_id, symbol)`
- `get_observation_facts(phase_id, ...)`
- `get_latest_completed_phase(prefix)`

The helpers issue select/filter/order/limit operations only.

## Token-Efficiency Rationale

DB-1 preserves artifact lineage once in registry tables while extracting compact fields needed for common historical queries. Consumers can retrieve bounded rows for a phase, window, sector, symbol, or generic metric fact without loading full historical JSON artifacts into prompt context.

## Governance Boundary

DB-1 is observational and read-model-only. It does not alter prediction, trading, live ingestion, replay execution, topology persistence, governed activation, or existing HIST-LONG artifacts. The loader checks known forbidden governance flags and fails closed if source artifacts indicate prediction, trading, replay activation/execution, topology persistence, raw cache writes, or provider/API calls are enabled.

## No-Prediction / No-Trading / No-Live-Ingestion Certification

Certified for this phase:

- No prediction logic was added or modified.
- No trading logic was added or modified.
- No live ingestion logic was added or modified.
- No FMP/provider calls are made by DB-1 loaders or query helpers.
- No HIST-LONG execution path is invoked.
- No existing historical artifacts are mutated.
- No destructive database operation is introduced.

## Next-Step Recommendation

Run the DB-1 loader in dry-run mode against current completed artifacts, review row counts and lineage checksums, then apply the migration in Supabase. Future HIST-LONG phases should write normalized metrics to `sefi_observation_facts` directly, while specialized tables may remain as convenience read models for existing consumers.
