# 11 — Architecture Gaps Audit

## Audit Scope

This audit reviewed the current source pack files `01` through `10` and the architecture diagrams under `whitepaper_source_pack/diagrams/`. It does not rewrite the source pack and does not infer architecture beyond documented repository evidence.

## Phase 4.5 correction note
This file now records the corrected status of the high-priority audit findings. Items marked corrected have been normalized in the source notes and diagrams; remaining ambiguities are limited to explicitly documented local-artifact fallback, future persistence paths not yet implemented, and source-row-dependent taxonomy values.

## Architecture Corrections Status

| Relationship | Phase 4.5 status | Evidence in corrected source pack | Residual ambiguity | Remaining action |
|---|---:|---|---|---|
| DB-2 ↔ Historical Intelligence | Corrected | `04` and `05` now distinguish fact-like rows, DB-2 fact candidates, persisted DB-2 facts, contribution, consumption, and retrieval. The historical stack diagram no longer implies a single linear pipe. | Historical local-artifact fallback remains bounded and labeled rather than promoted to source-of-truth status. | Keep future docs aligned to the producer/contributor/consumer/retriever distinction. |
| DB-2 ↔ OPS-LIVE | Corrected | `06` and `ops_live_architecture.md` now show OPS-LIVE-2 as the DB-2 emission path and OPS-LIVE-3 as read-only structural-state synthesis over DB-2 rows or bounded local fact rows. | No separate governed snapshot-persistence path is documented. | Treat OPS-LIVE-3 reports as local artifacts unless a future governed persistence contract is added. |
| OPS-LIVE ↔ OBS-QUERY | Corrected | `06` now maps OPS-LIVE-1 observations, OPS-LIVE-2 persisted live facts, and OPS-LIVE-3 snapshots through Structural State, OBS-QUERY, and Consumption Products. | OBS-QUERY retrieves DB-2 rows; OPS-LIVE-3 local snapshots may inform presentation context but are not DB-2 facts. | Do not imply OPS-LIVE-3 output is queryable through OBS-QUERY unless persisted by a future governed path. |
| OBS-QUERY ↔ Consumption Products | Fully documented | OBS-QUERY-4 creates analyst consumption views; Daily Briefing adapter consumes OBS-QUERY/HIST-INTEL artifacts; downstream pages are presentation-only. | Minor residual ambiguity: Consumption Products can also read HIST-INTEL style artifacts directly, which bypasses the purely OBS-QUERY-first narrative. | Document the allowed direct HIST-INTEL fallback path and precedence order between OBS-QUERY artifacts and HIST-INTEL artifacts. |
| Historical Intelligence ↔ OBS-QUERY | Corrected | `05` now includes a handoff table from historical outputs to OBS-QUERY filters, question types, comparison types, consumption views, and traceability. | Exact taxonomy values remain source-row dependent because DB-2 stores metric names rather than a separate taxonomy table. | Keep examples tied to observed `metric_name`, `phase_id`, and payload fields. |
| OBS-QUERY ↔ Governance | Corrected | `07`, `08`, and `09` now list governance certification field families and retrieval-only/no-prediction/no-recommendation guarantees. | Field presence varies by OBS-QUERY phase because retrieval, comparison, consumption, and validation certify different modes. | Preserve phase-specific fields while retaining the shared disabled-action guarantees. |
| DB-2 ↔ Governance | Fully documented | Fact emission validates context, required fields, bounded payloads, metric values, duplicate keys, dry-run defaults, and explicit write gates. | No major architectural gap, but DB-1/DB-2 naming remains a consistency issue. | Resolve naming in the data-model notes and migration-comment discussion. |
| Consumption Products ↔ Governance | Fully documented | Consumption Products are presentation-only, read-only, and constrained by Quality Gate filters and no-prediction/no-recommendation boundaries. | Top-level cards omit raw Evidence Reference identifiers while Story Detail preserves drill-down IDs; this is governed, but readers may misinterpret traceability as absent from all presentation surfaces. | Clarify that evidence is not always displayed at top level but remains available through drill-down models. |
| Source Universe ↔ OPS-LIVE-1 | Partially documented | OPS-LIVE-1 uses a DB-preferred universe table with validated config fallback and telemetry. | The source-of-truth priority during fallback/cutover is under-specified for audit readers. | Define the source-universe precedence rule and required telemetry when fallback occurs. |
| Structural State ↔ Queryable Intelligence | Corrected | `06`, `10`, and lifecycle diagrams now distinguish persisted DB-2 facts, non-persisted structural-state snapshots, and presentation-only items. | Historical structural-state terms can still appear in local artifacts before persistence. | Label local artifacts and fixtures explicitly when not persisted. |

## Ambiguities

| Ambiguity | Affected documents | Phase 4.5 status | Residual guidance |
|---|---|---|---|
| DB-2 position relative to Historical Intelligence | `01`, `02`, `04`, `05`, `10`, diagrams | Corrected by distinguishing local fact-like rows, DB-2 fact candidates, persisted DB-2 facts, contribution, consumption, and retrieval. | Avoid a single linear chain when the relationship is cyclic across build/read phases. |
| OPS-LIVE-3 persistence semantics | `06`, `diagrams/ops_live_architecture.md` | Corrected: OPS-LIVE-3 is read-only synthesis and produces local snapshot/report output rather than DB-2 facts. | Treat snapshots/reports as local artifacts unless a future governed persistence path names a table/path. |
| Evidence as conceptual layer vs database object | `03`, `04`, `10`, `diagrams/data_model_relationships.md` | The conceptual model says Observation → Fact → Evidence, but Evidence Reference identifiers are payload-level/canonicalized identifiers, not a dedicated DB-2 evidence table. | Use “Evidence Reference” for payload/derived identifiers unless a dedicated evidence table exists. |
| Fact-like rows vs DB-2 rows | `03`, `05`, `07`, `10` | Corrected by lifecycle definitions for Local Fixture, Fact-Like Row, DB-2 Fact Candidate, and Persisted DB-2 Fact. | Keep future source-pack updates aligned to those lifecycle state names. |
| Observation vs Observation Fact ownership | `02`, `03`, `04`, `06` | Corrected through DB-2 directionality and lifecycle sections that identify producers and consumers by state. | Use lifecycle states instead of adding parallel ownership terminology. |
| Live Intelligence vs OPS-LIVE terminology | `01`, `02`, `03`, `06` | Corrected in terminology notes: OPS-LIVE is the subsystem; Live Intelligence is the architectural capability/output category. | Preserve that distinction in future prose. |
| Queryable Intelligence vs OBS-QUERY terminology | `01`, `02`, `03`, `07` | Corrected in terminology notes: OBS-QUERY is the subsystem/interface; Queryable Intelligence is the fact-backed capability/output class. | Preserve that distinction in future prose. |
| Story vs Narrative Evolution terminology | `03`, `05`, `08` | Corrected: Narrative Evolution is reserved for HIST-INTEL historical outputs and Story Evolution for consumption-layer presentation history. | Avoid using Story Evolution for historical regime outputs. |
| Quality Gate scope | `03`, `08`, `09` | Corrected: Quality Gate is scoped to presentation filtering and Validation Scorecard is scoped to OBS-QUERY-5 checks. | Preserve separate terms for presentation suppression vs validation. |
| Source-of-truth scope | `04`, `08`, `09`, `10` | Corrected with Source of Truth Boundaries in DB-2, Governance, and Data Model notes. | Local artifacts remain governed inputs, not competing sources of truth. |
| Unsupported filters and payload fields | `04`, `07`, `10` | Sector/subsector/min-confidence are unsupported in OBS-QUERY-1 because not exposed as columns, yet these fields may exist in payloads or other tables. | Clarify which filters are first-class DB-2 columns, which are payload-only, and which are intentionally unsupported. |
| DB-1 vs DB-2 naming | `04`, `10` | The source pack notes legacy DB-1 historical read-model terminology while presenting `sefi_observation_facts` as DB-2. | Add a naming note that DB-2 is the current architectural name for observation-fact retrieval, while some migrations/comments retain legacy DB-1 labels. |

## Architectural Consistency Review

### Layer Definitions

- **Consistent:** Observation, Fact, Query, Consumption, and Governance are repeatedly defined with clear no-write/no-provider/no-prediction boundaries where applicable.
- **Corrected nuance:** Historical Intelligence and DB-2 are not strictly linear. Historical producers feed DB-2 through governed candidates, and DB-2/fact rows can enable fact-native historical findings and OBS-QUERY comparison.
- **Corrected:** OPS-LIVE-3 is now documented and diagrammed as read-only synthesis; OPS-LIVE-2 is the live DB-2 emission path.

### Data Flow

- **Consistent:** The dominant flow is bounded observation → observation fact → DB-2 → OBS-QUERY → consumption.
- **Corrected with bounded residuals:** Historical and live paths both converge on DB-2 through governed fact candidates; local artifacts, fixtures, and OPS-LIVE-3 snapshots are explicitly non-source-of-truth unless persisted by a governed path.
- **Corrected:** `historical_intelligence_stack.md` now shows completed local historical artifacts feeding HIST-LONG-8/9 and HIST-FACT candidates, with HIST-INTEL consuming/grouping local facts and DB-2 retrieving persisted facts without a simple one-way pipe.

### Governance Boundaries

- **Consistent:** No prediction, recommendation, trading, provider calls, and query/presentation writes are consistently prohibited.
- **Corrected:** `07` and `09` now list governance certification field families and shared disabled-action guarantees; phase-specific field variation remains intentional.

### Retrieval Boundaries

- **Consistent:** OBS-QUERY is retrieval-only over DB-2 rows or controlled fixtures.
- **Corrected:** `10` separates Local Artifact, Local Fixture, Fact-Like Row, DB-2 Fact Candidate, Persisted DB-2 Fact, and Presentation Item lifecycle states.

### Source-of-Truth Definitions

- **Consistent:** `sefi_observation_facts` is the source of truth for OBS-QUERY fact retrieval.
- **Corrected:** `04`, `09`, and `10` scope DB-2, governed local artifact, retrieval, and presentation boundaries explicitly.

## Documentation Completeness Score

Scores use a 1–10 scale for completeness, clarity, and traceability.

| Section | Completeness | Clarity | Traceability | Rationale |
|---|---:|---:|---:|---|
| 01 — Executive Overview | 8 | 8 | 7 | Strong system summary and governance posture; limited detail on cyclic DB-2/Historical relationships and source-of-truth scope. |
| 02 — System Evolution | 7 | 7 | 6 | Good layer progression, but the linear sequence oversimplifies bidirectional producer/consumer relationships. |
| 03 — Core Concepts | 8 | 8 | 7 | Useful canonical concept list; needs stricter distinction between conceptual terms and implementation subsystem names. |
| 04 — DB-2 Architecture | 8 | 8 | 9 | Strong lifecycle, gates, lineage, and retrieval notes; ambiguity remains around DB-2 order relative to Historical Intelligence. |
| 05 — Historical Intelligence | 8 | 7 | 8 | Detailed layer map and governance; package split and DB-2 contribution/consumption relationship need clearer architecture summary. |
| 06 — OPS-LIVE | 8 | 8 | 8 | Clear OPS-LIVE-1/2/3 responsibility split; diagram conflict around OPS-LIVE-3 persistence should be resolved. |
| 07 — OBS-QUERY | 9 | 9 | 8 | Strong retrieval-only contract and component map; certification schema and fixture-vs-production usage could be more explicit. |
| 08 — Consumption Products | 8 | 8 | 7 | Clear presentation-only boundary and product components; direct HIST-INTEL artifact fallback and evidence-display scope need clarification. |
| 09 — Governance | 9 | 8 | 8 | Strong cross-cutting governance model; would benefit from canonical certification fields and boundary ownership table. |
| 10 — Data Model | 8 | 8 | 9 | Strong table and identifier notes; DB-1/DB-2 naming and evidence-as-reference status need sharper treatment. |

## Whitepaper Readiness Assessment

| Use case | Readiness | Assessment |
|---|---|---|
| Professional whitepaper | Medium-high | The source pack is architecturally rich and evidence-grounded, but should resolve DB-2/Historical ordering, OPS-LIVE-3 diagram semantics, evidence terminology, and source-of-truth scoping before being turned into a polished whitepaper. |
| Internship documentation | High | The documents are strong for explaining subsystem responsibilities and governance. Add a glossary and producer/consumer matrix to improve onboarding. |
| Technical architecture review | Medium-high | Most boundaries are reviewable, especially DB-2, OBS-QUERY, and Governance. Remaining review blockers are unclear state persistence contracts and inconsistent diagrams. |
| Onboarding documentation | Medium | Core concepts are well described, but new readers may struggle with subsystem acronyms, historical phase names, and the distinction between artifacts, fixtures, fact-like rows, and persisted DB-2 facts. |

### Remaining Gaps

1. A canonical producer/consumer matrix across Observation, Fact, Evidence Reference, Structural State, Query Result, and Consumption View.
2. A canonical terminology standard separating conceptual capabilities from implementation subsystem names.
3. A corrected or annotated OPS-LIVE diagram showing OPS-LIVE-3 read-only semantics.
4. A corrected or annotated Historical Intelligence diagram matching the documented HIST-LONG → HIST-FACT → HIST-INTEL progression.
5. A field-level contract from HIST-FACT/HIST-INTEL to DB-2 and OBS-QUERY.
6. A field-level contract for OBS-QUERY governance certifications.
7. A source-of-truth scoping rule for DB-2 vs governed local artifacts.
8. A persistence rule for structural-state snapshots.
9. A distinction between OBS-QUERY-5 validation and runtime query/consumption flow.
10. A terminology note for legacy DB-1 references versus current DB-2 architecture.

## Top 10 Highest-Priority Documentation Improvements

1. Resolve DB-2 ↔ Historical Intelligence directionality with a non-linear producer/consumer diagram.
2. Keep `ops_live_architecture.md` aligned so OPS-LIVE-3 cannot be interpreted as writing structural snapshots to DB-2.
3. Fix `historical_intelligence_stack.md` so HIST-LONG, HIST-FACT, HIST-INTEL, DB-2, and OBS-QUERY ordering matches the source notes.
4. Add a source-of-truth scoping statement: DB-2 for OBS-QUERY facts; governed local artifacts only as documented inputs/fallbacks.
5. Rename or qualify “Evidence” as “Evidence Reference” where no evidence table exists.
6. Add a handoff table mapping historical taxonomy/persistence/drift/recurrence/stability fields to OBS-QUERY filters and typed questions.
7. Add a handoff table mapping OPS-LIVE-3 structural-state snapshot fields to downstream consumers.
8. Document governance certification fields emitted by OBS-QUERY and consumption outputs.
9. Standardize subsystem/capability terminology: OPS-LIVE vs Live Intelligence, OBS-QUERY vs Queryable Intelligence, Story vs Narrative Evolution.
10. Add lifecycle states for local artifact, local fixture, fact-like row, DB-2 fact candidate, persisted DB-2 fact, and presentation item.
