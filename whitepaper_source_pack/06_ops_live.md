# 06 — OPS-LIVE Source Notes

## Purpose
OPS-LIVE is the controlled live-observation path that moves from bounded operational ingestion to DB-2 observation facts and then to a read-only live structural state snapshot.

Repository anchors: `transmission_layers/expectation_failure/real_data/ops_live1_controlled_ecosystem_ingestion.py`, `sefi_observation_universe.py`, `transmission_layers/live_ops/ops_live2_observation_fact_accumulation.py`, `ops_live3_structural_state_snapshot.py`, `transmission_layers/history_read_model/fact_emitter.py`, `observation_fact_retrieval.py`.

## Architecture
Daily Observation → DB-2 fact candidate / persisted Observation Fact → Structural State → OBS-QUERY / Queryable Intelligence.

OPS-LIVE-1 captures bounded source observations. OPS-LIVE-2 converts those observations into DB-2 facts. OPS-LIVE-3 synthesizes accumulated facts into a bounded live structural state. DB-2 and OBS-QUERY make the state queryable without live provider calls during retrieval.

## OPS-LIVE-1 — controlled live ecosystem ingestion

### Purpose
OPS-LIVE-1 performs controlled operational observation over a bounded symbol universe. The current implementation includes a probe path and a controlled 50-symbol ingest path.

### Ingestion
- Uses FMP endpoint strategy `legacy_quote_then_stable_batch_quote` through an injected fetcher or API-key-backed fetcher.
- Builds canonical payloads and normalized operational surfaces from returned quote rows.
- Supports explicit snapshot date/output path inputs.
- Treats the operation as observation, not DB-2 emission.

### Source universe
- `OPS_LIVE1B_UNIVERSE` is capped by `OPS_LIVE1B_UNIVERSE_CAP = 50`.
- `sefi_observation_universe.py` provides the DB-preferred SEFI universe table contract and a validated config fallback.
- The universe table stores active symbols with entity, asset-class, sector/subsector, ecosystem group, source phase, universe version, and timestamps.

### Operational controls
- Fetcher injection enables deterministic tests and bounded ingestion.
- Missing API keys fail rather than silently expanding provider behavior.
- Universe validation checks active count, uniqueness, duplicates, digest, schema columns, and bounded sample symbols.
- DB universe loading falls back to validated config only when the DB source is unavailable or invalid.

### Governance
- OPS-LIVE-1 boundaries keep ingestion controlled, bounded, and observational.
- It does not persist DB-2 facts directly; fact persistence is delegated to OPS-LIVE-2.
- The source-universe migration is staged and does not modify existing active loaders outside the SEFI universe table.

### Inputs
Controlled universe symbols, optional DB universe rows, FMP/API fetcher output, snapshot date, and configuration fallback metadata.

### Outputs
Canonical live observation payloads, normalized operational surfaces, source-universe rows/telemetry, and ingestion/review summaries.

### Consumers
OPS-LIVE-2, operator review payloads, source-universe validation tests, and future controlled observation workflows.

### Governance boundaries
No unbounded source expansion, no DB-2 fact writes in OPS-LIVE-1, no prediction/trading/portfolio action, and no OBS-QUERY retrieval side effects.

## OPS-LIVE-2 — controlled live observation fact accumulation

### Purpose
OPS-LIVE-2 normalizes live observations and emits them as DB-2 `sefi_observation_facts` rows with optional parent artifact/run registry rows.

### Observation accumulation
- Accepts bounded live observations with `observed_at`, `source_phase`, `source_run_id`, entity fields, metric fields, and payload metadata.
- Caps local input rows with `MAX_LOCAL_INPUT_ROWS`.
- Normalizes string fields and metric values before fact construction.

### Fact accumulation
- Builds an explicit emission context with `phase_id = OPS-LIVE-2`, `phase_name`, `artifact_id`, `run_id`, `enabled`, and `dry_run`.
- Creates fact rows through the DB-2 fact emitter using deterministic duplicate-prevention keys.
- Emits parent `sefi_artifact_registry` and `sefi_run_registry` rows only when fact rows exist.
- Uses duplicate-ignore upsert behavior for idempotent accumulation.

### DB-2 emission
Writes require `enabled=True`, `dry_run=False`, and an injected database client. Without those conditions, OPS-LIVE-2 returns a dry-run report rather than mutating DB-2.

### Observation lifecycle
1. A live operational observation is received from OPS-LIVE-1 or a bounded local fixture.
2. OPS-LIVE-2 normalizes it into an observation fact candidate.
3. The fact emitter validates payload size, numeric/null metric value, required lineage fields, and duplicate key.
4. The row is dry-run summarized or appended/upserted into `sefi_observation_facts`.
5. OBS-QUERY can later retrieve the fact with fact/evidence lineage.

### Inputs
Live observations, context fields, optional client, write gates, artifact/run IDs, and bounded payload metadata.

### Outputs
DB-2 fact rows, artifact/run registry rows, insertion summaries, duplicate summaries, and governance review fields.

### Consumers
DB-2, OPS-LIVE-3, OBS-QUERY-1, historical/live comparison, consumption views, and validation harnesses.

### Governance boundaries
Dry-run default; explicit write gate; no provider calls inside accumulation; no prediction, trading, replay execution, topology persistence, schema migration, or core Supabase-client creation.

## OPS-LIVE-3 — live structural state snapshot

### Purpose
OPS-LIVE-3 reads accumulated live observation facts and synthesizes a bounded structural-state snapshot.

### Structural state synthesis
- Reads from `sefi_observation_facts` or bounded local fact rows.
- Classifies ingestion completeness, provider health, weakness pressure, replay pressure, contradiction pressure, concentration pressure, and overall live health.
- Fails closed to `INSUFFICIENT_DATA` when facts or metrics are missing.

### Ecosystem snapshotting
- Summarizes latest observed time, entity coverage, source-run coverage, metric counts, inspected fact count, and source digest.
- Carries an observation fact summary so downstream reviewers can understand the source set.

### State representation
The snapshot represents state as deterministic classes and metric values: `snapshot_status`, `live_health_class`, dimension classifications, coverage counts, latest observed timestamp, source coverage, metric counts, and governance review.

### Inputs
DB-2 fact rows from `sefi_observation_facts` or bounded local facts, plus retrieval limits.

### Outputs
Snapshot object, state summary, markdown report, classification fields, source digest, and governance review. OPS-LIVE-3 does not write to DB-2, does not emit fact rows, and does not create queryable DB-2 facts. Any JSON or markdown report produced by a runner is a local artifact for review/presentation, not a persisted source-of-truth fact. Its structural-state classifications are synthesis over existing facts or bounded local fact rows.

### Persistence semantics
| Question | OPS-LIVE-3 behavior |
| --- | --- |
| Writes to DB-2? | No. Governance review sets fact emission, schema changes, destructive operations, and core Supabase client creation to disabled. |
| Produces local artifacts? | It can return a snapshot/report object, and runners may serialize that object, but the artifact is local presentation/review output. |
| Creates queryable facts? | No. Queryable facts are OPS-LIVE-2 or historical rows persisted in `sefi_observation_facts`; OPS-LIVE-3 only reads those facts or bounded local fact rows. |
| Synthesis layer only? | Yes. It classifies live health/pressure dimensions from existing fact rows and source digest metadata without ingestion, replay, prediction, trading, topology mutation, or fact emission. |

### Consumers
OBS-QUERY source pack, live monitoring dashboards, historical/live comparison, and read-only consumption products.

### Governance boundaries
Read-only fact-native synthesis; no ingestion, no replay, no prediction, no trading, no topology mutation, no fact emission, and no database write.

## OPS-LIVE to Consumer handoff
| OPS-LIVE output | Structural State | OBS-QUERY | Consumption Products |
| --- | --- | --- | --- |
| OPS-LIVE-1 bounded operational observations | Not yet structural state; source observations for accumulation. | Not directly queryable as DB-2 facts unless OPS-LIVE-2 emits them. | Operator review payloads may be local inputs, not source-of-truth facts. |
| OPS-LIVE-2 persisted live observation facts (`phase_id = OPS-LIVE-2`, `live_*` metrics) | Input rows for OPS-LIVE-3 live health, coverage, pressure, and source-digest classes. | OBS-QUERY-1 retrieves by source layer/taxonomy/symbol/Evidence Reference identifier; OBS-QUERY-3 compares live rows with historical rows. | OBS-QUERY-4 and Daily Briefing can show live-only anomalies, historical/live deviations, and investigation candidates with fact and Evidence Reference drill-down. |
| OPS-LIVE-3 snapshot/report | Bounded live structural-state synthesis; not a fact emitter. | Can inform source-pack and dashboard interpretation, but does not add rows for OBS-QUERY retrieval. | May be presented as local review context; consumption products must not treat it as a persisted DB-2 fact. |

## Daily Observation to OBS-QUERY / Queryable Intelligence
1. **Daily Observation**: OPS-LIVE-1 produces bounded operational observations over a controlled universe.
2. **Observation Fact**: OPS-LIVE-2 emits governed DB-2 facts with lineage and duplicate-prevention keys when write gates pass.
3. **Structural State**: OPS-LIVE-3 reads accumulated facts and creates a bounded live health/state snapshot without persistence.
4. **OBS-QUERY / Queryable Intelligence**: OBS-QUERY retrieves DB-2 facts and exposes typed questions, comparisons, and consumption views without provider calls or writes.

## Architectural ambiguities
- OPS-LIVE-1 implementation lives under `expectation_failure/real_data`, while OPS-LIVE-2/3 live under `live_ops`.
- OPS-LIVE-1's canonical payloads are operational observations; DB-2 persistence starts in OPS-LIVE-2.
- Source-universe DB cutover has a validated fallback path, so consumers must distinguish DB universe source from config fallback telemetry.
