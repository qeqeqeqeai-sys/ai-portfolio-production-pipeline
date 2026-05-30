# 11 — Architecture Gaps Audit

## Audit Scope

This audit reviewed the current source pack files `01` through `10` and the architecture diagrams under `whitepaper_source_pack/diagrams/`. It does not rewrite the source pack and does not infer architecture beyond documented repository evidence.

## Missing Architectural Links

| Relationship | Status | Evidence in source pack | Gap or risk | Recommended clarification |
|---|---:|---|---|---|
| DB-2 ↔ Historical Intelligence | Partially documented | DB-2 is the central fact store; Historical Intelligence contributes historical artifacts/facts into DB-2 and supplies fields used by OBS-QUERY. | Direction is inconsistent. Some text places DB-2 before Historical Intelligence, while Historical Intelligence also produces rows loaded into DB-2. The historical diagrams also imply a sequence that can be read as HIST-INTEL before DB-2, while other sections describe DB-2 as the read model enabling fact-native historical findings. | State the relationship as bidirectional-but-asymmetric: Historical loaders/emitters produce DB-2 facts; historical intelligence may consume DB-2/fact-like rows for fact-native findings; DB-2 remains the source of truth for OBS-QUERY retrieval, not necessarily for every upstream historical artifact. |
| DB-2 ↔ OPS-LIVE | Partially documented | OPS-LIVE-2 emits live observations to `sefi_observation_facts`; OPS-LIVE-3 reads accumulated facts and produces structural state. | Text is clear, but `ops_live_architecture.md` shows OPS-LIVE-3 flowing into DB-2 as well as OPS-LIVE-2 flowing into DB-2, which can imply snapshot writes to DB-2. | Correct or annotate the diagram so OPS-LIVE-3 is explicitly read-only from DB-2 and emits snapshots/reports outside DB-2 fact persistence unless a separate governed snapshot persistence path exists. |
| OPS-LIVE ↔ OBS-QUERY | Partially documented | OPS-LIVE produces live facts/state; OBS-QUERY retrieves facts and performs historical/live comparison. | The handoff of OPS-LIVE-3 structural-state snapshots to OBS-QUERY is not precisely defined. It is unclear whether OBS-QUERY reads only DB-2 fact rows, local snapshot artifacts, or both when live structural state is involved. | Add an explicit contract for live state consumption: source object, allowed fields, whether it is DB-backed or artifact-backed, and how supporting fact IDs/evidence IDs are preserved. |
| OBS-QUERY ↔ Consumption Products | Fully documented | OBS-QUERY-4 creates analyst consumption views; Daily Briefing adapter consumes OBS-QUERY/HIST-INTEL artifacts; downstream pages are presentation-only. | Minor residual ambiguity: Consumption Products can also read HIST-INTEL style artifacts directly, which bypasses the purely OBS-QUERY-first narrative. | Document the allowed direct HIST-INTEL fallback path and precedence order between OBS-QUERY artifacts and HIST-INTEL artifacts. |
| Historical Intelligence ↔ OBS-QUERY | Partially documented | Historical Intelligence supplies phase IDs, metric names, taxonomy labels, persistence/drift/recurrence/stability payloads, fact IDs, evidence IDs, artifact IDs, and run IDs that OBS-QUERY retrieves. | The source pack does not fully map HIST-INTEL output fields to OBS-QUERY filters, typed questions, and comparison keys. | Add a field-level handoff table from HIST-FACT/HIST-INTEL outputs to OBS-QUERY canonical fields. |
| OBS-QUERY ↔ Governance | Fully documented | OBS-QUERY certifications disable provider calls, writes, schema migrations, fact creation, prediction, recommendation, and market actions. | The exact certification object/schema is not documented in the source pack. | Add a compact schema excerpt or field list for governance certification outputs. |
| DB-2 ↔ Governance | Fully documented | Fact emission validates context, required fields, bounded payloads, metric values, duplicate keys, dry-run defaults, and explicit write gates. | No major architectural gap, but DB-1/DB-2 naming remains a consistency issue. | Resolve naming in the data-model notes and migration-comment discussion. |
| Consumption Products ↔ Governance | Fully documented | Consumption Products are presentation-only, read-only, and constrained by quality gates and no-prediction/no-recommendation boundaries. | Top-level cards omit raw evidence IDs while Story Detail preserves drill-down IDs; this is governed, but readers may misinterpret traceability as absent from all presentation surfaces. | Clarify that evidence is not always displayed at top level but remains available through drill-down models. |
| Source Universe ↔ OPS-LIVE-1 | Partially documented | OPS-LIVE-1 uses a DB-preferred universe table with validated config fallback and telemetry. | The source-of-truth priority during fallback/cutover is under-specified for audit readers. | Define the source-universe precedence rule and required telemetry when fallback occurs. |
| Structural State ↔ Queryable Intelligence | Partially documented | Structural state is a bridge between facts and analyst questions. OPS-LIVE-3 and historical layers classify state; OBS-QUERY retrieves and compares facts. | It is unclear which structural-state outputs are persisted, retrieved, or merely generated as reports/snapshots. | Distinguish persisted observation facts, non-persisted structural-state snapshots, and presentation-only derived state. |

## Ambiguities

| Ambiguity | Affected documents | Issue | Recommended clarification |
|---|---|---|---|
| DB-2 position relative to Historical Intelligence | `01`, `02`, `04`, `05`, `10`, diagrams | DB-2 is described as both downstream of fact emission and before Historical Intelligence, while Historical Intelligence also contributes facts into DB-2. | Describe DB-2 as the canonical observation-fact read model that receives emissions from historical/live producers and is later consumed by query/historical-live comparison. Avoid a single linear chain when the relationship is cyclic across build/read phases. |
| OPS-LIVE-3 persistence semantics | `06`, `diagrams/ops_live_architecture.md` | Text says OPS-LIVE-3 reads facts and has no DB writes; the diagram can be read as OPS-LIVE-3 writing to DB-2. | Mark OPS-LIVE-3 as read-only from DB-2, with outputs as snapshots/reports unless separately persisted under a named table/path. |
| Evidence as conceptual layer vs database object | `03`, `04`, `10`, `diagrams/data_model_relationships.md` | The conceptual model says Observation → Fact → Evidence, but evidence IDs are payload-level/canonicalized identifiers, not a dedicated DB-2 evidence table. | Use “Evidence Reference” for payload/derived IDs unless a dedicated evidence table exists. |
| Fact-like rows vs DB-2 rows | `03`, `05`, `07`, `10` | Historical layers produce fact-like rows and DB-2 rows, but the boundary between local fact fixtures, expanded facts, and persisted `sefi_observation_facts` is not always explicit. | Define three categories: local fact-like row, DB-2 observation fact candidate, persisted DB-2 observation fact. |
| Observation vs Observation Fact ownership | `02`, `03`, `04`, `06` | OPS-LIVE-1 produces observations, OPS-LIVE-2 emits facts, historical loaders/fact expanders also produce facts; ownership is distributed but not summarized in one place. | Add a producer/owner matrix for Observation, Observation Fact candidate, persisted Fact, Structural State, and Consumption View. |
| Live Intelligence vs OPS-LIVE terminology | `01`, `02`, `03`, `06` | “Live Intelligence” and “OPS-LIVE” are used closely; Live Intelligence is a conceptual layer while OPS-LIVE is the implementation path. | Standardize: OPS-LIVE is the subsystem; Live Intelligence is the architectural capability produced by OPS-LIVE. |
| Queryable Intelligence vs OBS-QUERY terminology | `01`, `02`, `03`, `07` | Queryable Intelligence is a conceptual capability; OBS-QUERY is the implementation interface. | Standardize: OBS-QUERY is the subsystem; Queryable Intelligence is the capability/output class. |
| Story vs narrative/evolution terminology | `03`, `05`, `08` | HIST-INTEL uses narrative evolution/regime transition language; Consumption Products use Story and Story Evolution. | Define narrative/regime outputs as historical intelligence source concepts and Story as a presentation grouping derived from existing artifacts. |
| Quality Gate scope | `03`, `08`, `09` | Quality Gate is described as a deterministic presentation filter; governance also references validation scorecards. Readers may conflate presentation quality gates with OBS-QUERY validation. | Reserve “Quality Gate” for presentation filtering and use “Validation Scorecard” for OBS-QUERY-5 checks. |
| Source-of-truth scope | `04`, `08`, `09`, `10` | DB-2 is source of truth for OBS-QUERY retrieval, while Consumption Products can load existing local artifacts. | State that DB-2 is the source of truth for OBS-QUERY fact retrieval; local artifacts are allowed presentation inputs only when already governed and traceable. |
| Unsupported filters and payload fields | `04`, `07`, `10` | Sector/subsector/min-confidence are unsupported in OBS-QUERY-1 because not exposed as columns, yet these fields may exist in payloads or other tables. | Clarify which filters are first-class DB-2 columns, which are payload-only, and which are intentionally unsupported. |
| DB-1 vs DB-2 naming | `04`, `10` | The source pack notes legacy DB-1 historical read-model terminology while presenting `sefi_observation_facts` as DB-2. | Add a naming note that DB-2 is the current architectural name for observation-fact retrieval, while some migrations/comments retain legacy DB-1 labels. |

## Architectural Consistency Review

### Layer Definitions

- **Consistent:** Observation, Fact, Query, Consumption, and Governance are repeatedly defined with clear no-write/no-provider/no-prediction boundaries where applicable.
- **Partially inconsistent:** Historical Intelligence and DB-2 are not strictly linear. Historical producers feed DB-2, but DB-2/fact rows also enable fact-native historical findings and OBS-QUERY comparison.
- **Contradiction flagged:** OPS-LIVE-3 is textually read-only but diagrammatically connected as if it may output into DB-2.

### Data Flow

- **Consistent:** The dominant flow is bounded observation → observation fact → DB-2 → OBS-QUERY → consumption.
- **Partially documented:** Historical and live paths both converge on DB-2, but historical artifact fallback and live structural-state snapshot handoffs are not fully specified.
- **Contradiction flagged:** `historical_intelligence_stack.md` shows HIST-INTEL flowing to HIST-LONG before DB-2, while source notes describe HIST-LONG as upstream of HIST-FACT/HIST-INTEL.

### Governance Boundaries

- **Consistent:** No prediction, recommendation, trading, provider calls, and query/presentation writes are consistently prohibited.
- **Needs precision:** The exact shape of governance certification outputs is described conceptually but not specified as a canonical field contract.

### Retrieval Boundaries

- **Consistent:** OBS-QUERY is retrieval-only over DB-2 rows or controlled fixtures.
- **Needs precision:** The allowed role of local fixtures and local artifacts in production vs validation vs presentation should be separated.

### Source-of-Truth Definitions

- **Consistent:** `sefi_observation_facts` is the source of truth for OBS-QUERY fact retrieval.
- **Needs precision:** Historical artifacts and consumption artifacts are valid inputs in some layers; their source-of-truth status should be scoped so they do not compete with DB-2.

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
2. Fix `ops_live_architecture.md` so OPS-LIVE-3 cannot be interpreted as writing structural snapshots to DB-2.
3. Fix `historical_intelligence_stack.md` so HIST-LONG, HIST-FACT, HIST-INTEL, DB-2, and OBS-QUERY ordering matches the source notes.
4. Add a source-of-truth scoping statement: DB-2 for OBS-QUERY facts; governed local artifacts only as documented inputs/fallbacks.
5. Rename or qualify “Evidence” as “Evidence Reference” where no evidence table exists.
6. Add a handoff table mapping historical taxonomy/persistence/drift/recurrence/stability fields to OBS-QUERY filters and typed questions.
7. Add a handoff table mapping OPS-LIVE-3 structural-state snapshot fields to downstream consumers.
8. Document governance certification fields emitted by OBS-QUERY and consumption outputs.
9. Standardize subsystem/capability terminology: OPS-LIVE vs Live Intelligence, OBS-QUERY vs Queryable Intelligence, Story vs Narrative Evolution.
10. Add lifecycle states for local artifact, local fixture, fact-like row, DB-2 fact candidate, persisted DB-2 fact, and presentation item.
