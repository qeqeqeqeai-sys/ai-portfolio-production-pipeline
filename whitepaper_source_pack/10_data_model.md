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

## Source of Truth Boundaries
| Boundary | Data-model interpretation |
| --- | --- |
| DB-2 scope | `sefi_observation_facts` is the persisted observation-fact table used as OBS-QUERY's source of truth. Parent artifact/run registry rows provide lineage, not replacement fact sources. |
| Governed local artifact scope | Historical JSON/markdown artifacts, local fact-like rows, controlled fixtures, and Daily Briefing inputs are bounded source or presentation artifacts until emitted through a governed DB-2 path. |
| Retrieval scope | OBS-QUERY result envelopes and Evidence References are read models over DB-2 rows or labeled fixtures; they do not define new database tables. |
| Presentation scope | Consumption cards, Story Evolution labels, Quality Gate counts, and investigation prompts are presentation items and are not persisted DB-2 facts. |

## Lifecycle state definitions
| State | Definition | Producer | Consumer | Governance role |
| --- | --- | --- | --- | --- |
| Local Artifact | Existing JSON/markdown/report artifact produced by historical, OBS-QUERY, or presentation code and read from local paths. | HIST-LONG/HIST-INTEL, OBS-QUERY writers, Daily Briefing loaders/runners. | Historical analysis, consumption adapters, reviewers. | Bounded input/output; not a DB-2 source of truth unless emitted as facts. |
| Local Fixture | Controlled in-memory or local rows used by tests, validation harnesses, dry runs, or fallback execution. | OBS-QUERY validation, local runners, bounded test helpers. | Retrieval/comparison/consumption tests and Validation Scorecard outputs. | Labeled fixture source; proves behavior without DB writes. |
| Fact-Like Row | Local row shaped like an observation fact, often carrying `fact_id`, metric fields, payload, lineage, or Evidence Reference identifiers before persistence. | HIST-LONG-8/9, HIST-FACT, HIST-INTEL fact-native paths, OPS-LIVE-2 dry runs. | Fact emitters, OBS-QUERY local mode, validation, historical analysis. | Candidate evidence carrier; not persisted until write gates pass. |
| DB-2 Fact Candidate | Validated row in `sefi_observation_facts` insert/upsert shape with deterministic duplicate key and required lineage. | DB-2 fact emitter, OPS-LIVE-2 accumulation, historical emission paths. | DB-2 write gate and dry-run summaries. | Must pass payload, metric, lineage, context, duplicate-key, client, enabled, and dry-run controls. |
| Persisted DB-2 Fact | Row stored in `sefi_observation_facts`. | Governed emission path with `enabled=True`, `dry_run=False`, and database client. | OBS-QUERY-1/2/3/4/5, OPS-LIVE-3, Consumption Products through OBS-QUERY. | Source-of-truth fact for retrieval; carries IDs, lineage, payload, and duplicate prevention. |
| Presentation Item | Briefing card, investigation candidate, Story Evolution highlight, Quality Gate summary, or Streamlit display item derived from existing outputs. | OBS-QUERY-4 and Daily Briefing adapter. | Analysts and Evidence Reference drill-down reviewers. | Read-only presentation; must preserve drill-down and avoid predictions/recommendations. |

## Fact identifiers
DB-2 uses two identifier patterns:

- Database `id` on `sefi_observation_facts`, used by retrieval as a fact ID when present.
- Deterministic `duplicate_prevention_key`, generated from phase, entity, metric, window, artifact, run, and payload identity. Historical fact-expansion layers also create stable local `fact_id` values in payload/output rows before DB emission.

OBS-QUERY canonicalization checks `id`, `fact_id`, and `duplicate_prevention_key` in that order, then falls back to payload identifiers when necessary.

## Evidence Reference identifiers
Evidence Reference identifiers are not a dedicated DB-2 table in the current migration. They are carried through `payload_jsonb` and retrieval canonicalization. OBS-QUERY reads `payload_jsonb.evidence_id` or related source-evidence fields, with fallback to row IDs or duplicate-prevention keys. Consumption outputs preserve supporting fact IDs and supporting Evidence Reference identifiers for drill-down.

## Source phases
Current source phases include historical phases such as `HIST-LONG-4`, `HIST-LONG-5B`, `HIST-LONG-6`, `HIST-LONG-7`, `HIST-LONG-8`, `HIST-LONG-9`, `HIST-FACT-1`, `HIST-FACT-2`, `HIST-INTEL-1`, `HIST-INTEL-1B`, `HIST-INTEL-2`, `HIST-INTEL-3`, `HIST-INTEL-4`, and live phases such as `OPS-LIVE-1`, `OPS-LIVE-2`, and `OPS-LIVE-3`. The exact persisted `phase_id` is supplied by each producer and retained on rows.

## Lineage fields
Core lineage fields are `phase_id`, `phase_name`, `artifact_id`, `run_id`, `created_at`, `loaded_at`, `completed_at` where applicable, `source_artifact_path`, `source_artifact_sha256`, `source_phase`, `source_run_id` in payloads, and `duplicate_prevention_key`. These fields bind each observation/fact to a governed phase, artifact, run, and source payload.

## Observation payloads
Observation payloads live in `payload_jsonb` and must remain mappings within bounded byte limits. They carry source-specific metadata such as `observed_at`, `source_phase`, `source_run_id`, `evidence_id`, symbols/tickers, classifications, values-by-window, stability/drift classes, and subsystem payload fields. Payloads are metadata and Evidence Reference carriers; unsupported schema details should not be inferred from them.

## Architectural ambiguities
- Evidence Reference identifiers are payload-level/canonicalized identifiers, not a separately migrated evidence table in the current DB-2 schema.
- The migration comment labels the schema as DB-1 historical read model, while existing source-pack documentation identifies `sefi_observation_facts` as DB-2's central fact table.
- Additional operational dashboard tables exist elsewhere, but they are not core to the current SEFI DB-2/OBS-QUERY data model described here.
