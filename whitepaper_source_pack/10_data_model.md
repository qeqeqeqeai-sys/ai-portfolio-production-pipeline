# 10 — SEFI Data Model Source Notes

## Purpose
This document describes only the current SEFI architecture evidenced in repository code and migrations. The central DB-2 table is `sefi_observation_facts`, supported by artifact/run lineage tables and current universe/read-model tables.

Repository anchors: `supabase/migrations/20260529000100_create_sefi_history_read_model.sql`, `20260529000200_create_sefi_observation_universe.sql`, `transmission_layers/history_read_model/fact_emitter.py`, `loader.py`, `observation_fact_retrieval.py`, `queries.py`, `transmission_layers/live_ops/ops_live2_observation_fact_accumulation.py`.

## Conceptual data model
Observation → Fact → Evidence → Retrieval → Consumption.

- **Observation**: bounded historical or live observation from a governed phase.
- **Fact**: normalized DB-2 row in `sefi_observation_facts` with phase, entity, metric, window, artifact, run, payload, and duplicate key.
- **Evidence**: evidence identifier carried in payloads or row IDs, plus artifact/run lineage.
- **Retrieval**: OBS-QUERY selects bounded fact rows and canonicalizes fact/evidence envelopes.
- **Consumption**: analyst views and daily briefing consume retrieved facts with drill-down identifiers.

## Major tables

### `sefi_observation_facts`
- **Purpose**: DB-2 source-of-truth table for bounded observation facts.
- **Producer**: `fact_emitter.py`, OPS-LIVE-2, and historical/read-model loaders that normalize observations into fact rows.
- **Consumer**: OBS-QUERY-1 retrieval, OBS-QUERY typed questions, historical/live comparison, consumption views, OPS-LIVE-3 snapshots.
- **Key fields**: `id`, `phase_id`, `phase_name`, `window_days`, `entity_type`, `entity_id`, `metric_name`, `metric_value`, `artifact_id`, `run_id`, `created_at`, `loaded_at`, `payload_jsonb`, `duplicate_prevention_key`.
- **Governance considerations**: append-only trigger, unique duplicate key, bounded JSON payload, foreign keys to artifact/run lineage, deterministic duplicate-key validation, dry-run/write gate in emitters, and no provider calls during retrieval.

### `sefi_artifact_registry`
- **Purpose**: register source artifacts and their SHA-256 identity.
- **Producer**: history read-model loader and OPS-LIVE-2 parent registry emission.
- **Consumer**: fact lineage, run registry, phase runs, audit/retrieval drill-down.
- **Key fields**: `artifact_id`, `source_artifact_path`, `source_artifact_sha256`, `artifact_kind`, `schema_version`, `created_at`, `loaded_at`, `payload_jsonb`, `duplicate_prevention_key`.
- **Governance considerations**: unique source path/SHA pair, SHA format check, bounded payload, append-only trigger, duplicate-prevention key.

### `sefi_run_registry`
- **Purpose**: register a governed execution/run for a phase and artifact.
- **Producer**: history read-model loader and OPS-LIVE-2 parent registry emission.
- **Consumer**: `sefi_observation_facts`, `sefi_phase_runs`, query lineage, and downstream audit.
- **Key fields**: `run_id`, `phase_id`, `phase_name`, `artifact_id`, `status`, `created_at`, `loaded_at`, `completed_at`, `payload_jsonb`, `duplicate_prevention_key`.
- **Governance considerations**: artifact foreign key, bounded payload, append-only trigger, duplicate-prevention key, explicit phase/run lineage.

### `sefi_phase_runs`
- **Purpose**: append-only phase-run ledger linking phases, artifacts, and runs.
- **Producer**: history read-model loader.
- **Consumer**: architecture/audit views requiring phase execution lineage.
- **Key fields**: `id`, `phase_id`, `phase_name`, `status`, `artifact_id`, `run_id`, `created_at`, `loaded_at`, `completed_at`, `payload_jsonb`, `duplicate_prevention_key`.
- **Governance considerations**: artifact/run foreign keys, bounded payload, append-only trigger, duplicate-prevention key.

### `sefi_hist_observations`
- **Purpose**: store generic historical observation payloads associated with source artifacts/runs.
- **Producer**: history read-model loader.
- **Consumer**: historical read-model users and audit paths.
- **Key fields**: `id`, `phase_id`, `phase_name`, `observation_type`, `observed_at`, `artifact_id`, `run_id`, `created_at`, `loaded_at`, `payload_jsonb`, `duplicate_prevention_key`.
- **Governance considerations**: append-only trigger, bounded payload, artifact/run foreign keys, duplicate-prevention key.

### `sefi_window_metrics`
- **Purpose**: store historical window-level metrics.
- **Producer**: history read-model loader from completed historical artifacts.
- **Consumer**: historical intelligence, DB-1/DB-2 read paths, and architecture reviews.
- **Key fields**: `id`, `phase_id`, `phase_name`, `window_days`, `completeness`, `replay_density`, `replay_saturation`, `contradiction_burden`, `sector_hhi`, `subsector_hhi`, `effective_symbol_count`, `artifact_id`, `run_id`, `payload_jsonb`, `duplicate_prevention_key`.
- **Governance considerations**: positive window check, append-only trigger, bounded payload, artifact/run lineage.

### `sefi_sector_morphology`
- **Purpose**: store morphology records by sector/subsector.
- **Producer**: history read-model loader from historical ecology artifacts.
- **Consumer**: historical intelligence, morphology analysis, and query/consumption context.
- **Key fields**: `id`, `phase_id`, `phase_name`, `morphology_type`, `sector`, `subsector`, `symbol_count`, `symbol_share`, `rank`, `artifact_id`, `run_id`, `payload_jsonb`, `duplicate_prevention_key`.
- **Governance considerations**: append-only trigger, bounded payload, duplicate-prevention key, artifact/run lineage.

### `sefi_symbol_metrics`
- **Purpose**: store symbol-level historical metrics.
- **Producer**: history read-model loader.
- **Consumer**: historical intelligence, symbol-specific retrieval helpers, and downstream source-pack analysis.
- **Key fields**: `id`, `phase_id`, `phase_name`, `symbol`, `window_days`, `metric_type`, `metric_value`, `artifact_id`, `run_id`, `payload_jsonb`, `duplicate_prevention_key`.
- **Governance considerations**: append-only trigger, bounded payload, duplicate-prevention key, artifact/run lineage.

### `sefi_observation_universe`
- **Purpose**: staged DB source for the active SEFI observation universe.
- **Producer**: `sefi_observation_universe.py` row builder/upsert path and migration.
- **Consumer**: OPS-LIVE-1 universe loading, validation tests, controlled observation ingestion.
- **Key fields**: `symbol`, `entity_name`, `entity_type`, `asset_class`, `sector`, `subsector`, `ecosystem_group`, `source_phase`, `universe_version`, `is_active`, `created_at`, `updated_at`.
- **Governance considerations**: primary key on `(symbol, universe_version)`, uppercase/nonblank symbol checks, active-symbol/source-version indexes, DB-preferred loader with validated config fallback, and no modification of legacy active loaders.

## Fact identifiers
DB-2 uses two identifier patterns:

- Database `id` on `sefi_observation_facts`, used by retrieval as a fact ID when present.
- Deterministic `duplicate_prevention_key`, generated from phase, entity, metric, window, artifact, run, and payload identity. Historical fact-expansion layers also create stable local `fact_id` values in payload/output rows before DB emission.

OBS-QUERY canonicalization checks `id`, `fact_id`, and `duplicate_prevention_key` in that order, then falls back to payload identifiers when necessary.

## Evidence identifiers
Evidence IDs are not a dedicated DB-2 table in the current migration. They are carried through `payload_jsonb` and retrieval canonicalization. OBS-QUERY reads `payload_jsonb.evidence_id` or related source-evidence fields, with fallback to row IDs or duplicate-prevention keys. Consumption outputs preserve supporting fact IDs and supporting evidence IDs for drill-down.

## Source phases
Current source phases include historical phases such as `HIST-LONG-4`, `HIST-LONG-5B`, `HIST-LONG-6`, `HIST-LONG-7`, `HIST-LONG-8`, `HIST-LONG-9`, `HIST-FACT-1`, `HIST-FACT-2`, `HIST-INTEL-1`, `HIST-INTEL-1B`, `HIST-INTEL-2`, `HIST-INTEL-3`, `HIST-INTEL-4`, and live phases such as `OPS-LIVE-1`, `OPS-LIVE-2`, and `OPS-LIVE-3`. The exact persisted `phase_id` is supplied by each producer and retained on rows.

## Lineage fields
Core lineage fields are `phase_id`, `phase_name`, `artifact_id`, `run_id`, `created_at`, `loaded_at`, `completed_at` where applicable, `source_artifact_path`, `source_artifact_sha256`, `source_phase`, `source_run_id` in payloads, and `duplicate_prevention_key`. These fields bind each observation/fact to a governed phase, artifact, run, and source payload.

## Observation payloads
Observation payloads live in `payload_jsonb` and must remain mappings within bounded byte limits. They carry source-specific metadata such as `observed_at`, `source_phase`, `source_run_id`, `evidence_id`, symbols/tickers, classifications, values-by-window, stability/drift classes, and subsystem payload fields. Payloads are metadata and evidence carriers; unsupported schema details should not be inferred from them.

## Architectural ambiguities
- Evidence IDs are payload-level/canonicalized identifiers, not a separately migrated evidence table in the current DB-2 schema.
- The migration comment labels the schema as DB-1 historical read model, while existing source-pack documentation identifies `sefi_observation_facts` as DB-2's central fact table.
- Additional operational dashboard tables exist elsewhere, but they are not core to the current SEFI DB-2/OBS-QUERY data model described here.
