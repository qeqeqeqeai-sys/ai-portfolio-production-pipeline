# 04 — DB-2 Architecture Source Notes

## Purpose
DB-2 is the repository's fact-native read model for SEFI observations. Its central table is `sefi_observation_facts`, an append-oriented store of bounded observation facts emitted from governed phases and later retrieved by OBS-QUERY and consumption products.

Repository anchors: `transmission_layers/history_read_model/fact_emitter.py`, `transmission_layers/live_ops/ops_live2_observation_fact_accumulation.py`, `transmission_layers/history_read_model/observation_fact_retrieval.py`, `transmission_layers/history_read_model/queries.py`.

## Architectural role
DB-2 is not a single linear stage before all Historical Intelligence. It is the persisted observation-fact boundary for rows that have passed a governed emission path. Historical layers can produce local fact-like rows and DB-2 fact candidates before persistence; DB-2 then stores persisted observation facts that OBS-QUERY and comparison layers retrieve. OPS-LIVE-2 also produces DB-2 fact candidates and can persist them when the explicit write gate is open. It converts source-layer observations into normalized rows with stable lineage fields: `phase_id`, `phase_name`, `artifact_id`, `run_id`, `entity_type`, `entity_id`, `metric_name`, `metric_value`, `window_days`, bounded `payload_jsonb`, and `duplicate_prevention_key`.

## Inputs
- Gated fact emission context: `enabled`, `dry_run`, `phase_id`, `phase_name`, `artifact_id`, `run_id`.
- Metric observations with entity, metric, optional window, value, and bounded payload.
- OPS-LIVE-2 bounded live observations containing `observed_at`, `source_phase`, `source_run_id`, entity fields, metric fields, and payload metadata.
- Parent registry metadata for artifact and run lineage.

## Outputs
- Deterministic rows for `sefi_observation_facts`.
- Optional parent `sefi_artifact_registry` and `sefi_run_registry` rows for OPS-LIVE-2 emissions.
- Emission summaries with attempted/inserted counts and duplicate handling.
- Canonical retrieval envelopes used by OBS-QUERY-1.

## Major components
- **Fact emitter**: validates context, normalizes strings, bounds payloads, computes duplicate keys, validates rows, and performs dry-run or insert/upsert emission.
- **OPS-LIVE-2 accumulation**: normalizes bounded live observations, builds DB-2 fact rows, emits parent registries, and gates writes by `enabled`, `dry_run`, and client presence.
- **Read query helpers**: expose direct table retrieval for phase, entity, window, and observation fact use cases.
- **OBS-QUERY-1 retrieval adapter**: canonicalizes retrieved rows into fact and Evidence Reference envelopes without synthesis.

## Observation Fact lifecycle
1. **Observation capture**: upstream live or historical components provide bounded observations.
2. **Emission context construction**: context must be explicitly enabled and include phase/artifact/run identity.
3. **Fact row construction**: observations are normalized into DB-2 row shape, including deterministic payload ordering and numeric/null metric validation.
4. **Lineage binding**: `artifact_id`, `run_id`, `phase_id`, `phase_name`, payload source fields, and `duplicate_prevention_key` bind each row to source execution lineage.
5. **Emission gate**: dry-run is the safe default; writes require explicit enablement, non-dry execution, and an injected database client.
6. **Accumulation**: rows are append-oriented; duplicate prevention supports idempotent accumulation through conflict handling on `duplicate_prevention_key`.
7. **Retrieval**: downstream layers select bounded rows from `sefi_observation_facts`, apply supported filters, and expose canonical facts plus Evidence References.

## Fact emission
Fact emission is deterministic and fail-closed:
- Context without `enabled=True` or missing required context fields emits no rows.
- Required row fields must be present.
- `metric_value` must be numeric or null.
- `payload_jsonb` must be a mapping and fit the configured byte bound.
- `duplicate_prevention_key` must match the deterministic hash of the row identity.

## Fact accumulation
OPS-LIVE-2 demonstrates accumulation semantics:
- It caps local input rows.
- It normalizes live observations into DB-2 observations.
- It creates parent artifact/run registry rows only when fact rows exist.
- It writes only when `enabled is True`, `dry_run is False`, and a client is supplied.
- It uses duplicate-ignore upsert behavior for idempotent accumulation.

## Fact retrieval
Retrieval is bounded and read-only:
- OBS-QUERY-1 reads selected DB-2 columns from `sefi_observation_facts`.
- Supported filters include snapshot date, symbol, source layer, taxonomy, Evidence Reference identifier, and limit.
- Unsupported filters such as sector, subsector, and minimum confidence are reported as unsupported because DB-2 fact rows do not expose those columns in the OBS-QUERY-1 schema.
- Returned rows are canonicalized with fact IDs, Evidence Reference identifiers, snapshot date, taxonomy, artifact/run lineage, and payload.

## Source-of-truth role
Repository code identifies `sefi_observation_facts` as the source of truth for OBS-QUERY fact retrieval and downstream query-derived consumption. OBS-QUERY governance certifications explicitly set `source_of_truth` to this table and disable provider calls, writes, schema migrations, prediction, recommendation, and market-action behavior. This statement is scoped to persisted DB-2 observation facts; it does not make every local artifact, fixture, presentation card, or report a source of truth.

## Source of Truth Boundaries
| Boundary | In scope | Out of scope |
| --- | --- | --- |
| DB-2 scope | Persisted rows in `sefi_observation_facts` plus required lineage fields, duplicate-prevention keys, and optional parent artifact/run registry rows emitted by governed DB-2 paths. | Local fact-like rows, markdown reports, presentation cards, quality summaries, and historical artifacts that have not been emitted into DB-2. |
| Governed local artifact scope | Completed historical artifacts, OBS-QUERY artifacts, validation fixtures, and Daily Briefing inputs used as bounded local inputs by analysis or presentation code. | Claims that these files are canonical DB facts or that their derived presentation fields are persisted DB-2 rows. |
| Retrieval scope | OBS-QUERY reads selected DB-2 columns or controlled local fixtures and returns canonical facts, Evidence References, unsupported-filter notices, and governance certification. | Provider calls, schema changes, DB writes, fact creation, forecast generation, recommendation generation, or unsupported synthetic fields. |
| Presentation scope | Consumption Products select, label, suppress, group, and display existing query/artifact items while preserving drill-down identifiers. | Creating new DB-2 facts, mutating artifacts, changing source-of-truth status, or making predictions/recommendations. |

## Fact lineage
Lineage is carried through:
- Row identity: `phase_id`, `phase_name`, `window_days`, entity fields, `metric_name`, `artifact_id`, `run_id`.
- Source metadata: `payload_jsonb` can carry `observed_at`, `source_phase`, `source_run_id`, `evidence_id`, identifiers, and subsystem payload fields.
- Registry lineage: OPS-LIVE-2 can emit parent artifact/run registry rows with source artifact path, source SHA-256, status, and duplicate prevention keys.
- Retrieval lineage: canonical outputs include `artifact_id`, `run_id`, `fact_id`, and `evidence_id`.

## Data flow
Observation Layer → bounded observations → emission context → normalized DB-2 fact candidates → optional parent registries → governed `sefi_observation_facts` accumulation when write gates pass → OBS-QUERY retrieval → historical/live comparison → consumption views.

## DB-2 and Historical Intelligence directionality
| Action | Repository-grounded owner | DB-2 relationship |
| --- | --- | --- |
| Produces local historical structure | HIST-LONG and HIST-INTEL layers inspect completed local artifacts and fact-like rows. | May precede DB-2 persistence and should not be described as reading only from DB-2. |
| Produces DB-2 fact candidates | HIST-FACT/HIST-LONG fact-expansion paths and OPS-LIVE-2 normalize observations into DB-2-shaped rows. | Candidate rows become DB-2 facts only after governed emission. |
| Contributes facts | Historical emitters and OPS-LIVE-2 can contribute rows to `sefi_observation_facts` when context, dry-run, and client gates allow it. | DB-2 accumulates contributed facts append-or-upsert style. |
| Retrieves facts | OBS-QUERY-1, OBS-QUERY-2, OBS-QUERY-3, OPS-LIVE-3, validation, and consumption views read DB-2 rows or bounded fixtures. | Retrieval is read-only and preserves fact IDs, Evidence Reference identifiers, artifact IDs, and run IDs. |
| Consumes facts | Historical/live comparison, typed questions, OPS-LIVE-3 structural-state synthesis, and Consumption Products consume persisted or fixture facts. | Consumption does not imply new persistence unless routed through a governed emitter. |

## Governance boundaries
- Dry-run default.
- Explicit write gate.
- No provider API calls inside fact emission/accumulation.
- No live ingestion side effects inside DB-2 accumulation beyond provided observations.
- No prediction, trading execution, replay execution, topology persistence, schema changes, or core Supabase client creation in OPS-LIVE-2 governance review.
- Payload boundedness and duplicate-key validation are enforced before emission.

## Downstream consumers
- OBS-QUERY-1 fact retrieval.
- OBS-QUERY-2 intelligence question retrieval.
- OBS-QUERY-3 historical/live comparison.
- OBS-QUERY-4 analyst consumption views.
- OBS-QUERY-5 validation fixture and scorecard.
- Daily Briefing and Investigation Queue adapters through OBS-QUERY-4 artifacts.

## Important implementation details
- `MAX_PAYLOAD_BYTES` bounds payload JSON size.
- Symbol entity IDs are uppercased; entity types and metric names are lowercased.
- Duplicate keys are SHA-256 hashes over table and row identity fields.
- OBS-LIVE-2 source digests produce deterministic default artifact/run IDs for local bounded payloads.
- Read paths order by loaded time, run ID, and row ID where available.

## Glossary of subsystem-specific terms
- **DB-2**: Fact-native observation read model centered on `sefi_observation_facts`.
- **Observation Fact**: A bounded, lineage-bearing row representing one observed metric/entity relationship.
- **Fact emission**: Deterministic conversion of observations into DB-2 insert rows.
- **Fact accumulation**: Append-oriented, duplicate-safe persistence of observation facts.
- **Duplicate prevention key**: Stable hash over row identity used for idempotence.
- **Payload JSONB**: Bounded metadata envelope for source/evidence details.
- **Parent registries**: Artifact/run registry rows that preserve source lineage for emitted facts.
