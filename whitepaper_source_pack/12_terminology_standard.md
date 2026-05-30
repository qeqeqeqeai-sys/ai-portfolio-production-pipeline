# 12 — Terminology Standard

## Purpose

This document defines canonical terminology for the SEFI source pack. It standardizes terms without adding unsupported architecture.

## Canonical Terms

| Term | Canonical definition | Approved abbreviations | Prohibited synonyms | Related terms |
|---|---|---|---|---|
| Observation | A bounded historical or live source signal captured before normalization into the DB-2 observation-fact shape. | Obs, source observation | raw prediction, signal recommendation, trade signal | Observation Fact, Evidence Reference, OPS-LIVE-1, HIST-LONG |
| Observation Fact | A normalized DB-2 row or fact-like row representing an observation with phase, entity, metric, value, window, payload, artifact, run, and duplicate-prevention lineage. | Fact, obs fact, DB-2 fact when persisted | generated insight, narrative fact, prediction fact | DB-2, Fact Lineage, Evidence Reference |
| Evidence | Source support associated with a fact or view item, currently represented as payload-level or canonicalized evidence identifiers, row IDs, duplicate-prevention keys, or supporting evidence ID lists. | Evidence ref, evidence ID | evidence table, proof table, source proof | Observation Fact, Fact Lineage, Story Detail |
| Fact Lineage | Identifiers and metadata binding a fact to producing phase, artifact, run, source payload, entity, metric, window, and duplicate-prevention identity. | Lineage, fact trace | provenance-free fact, anonymous finding | artifact_id, run_id, phase_id, duplicate_prevention_key |
| Structural State | A bounded classification of current or historical system condition derived from existing facts, such as live health classes, pressure dimensions, coverage summaries, or historical structural classifications. | State, structural snapshot when snapshot-specific | forecast state, trading state, recommendation state | OPS-LIVE-3, Historical Intelligence, Stability |
| Persistence | The degree to which a structure or signal remains present across historical windows or repeated fact sets. | Persistent structure | prediction durability, guaranteed continuation | Recurrence, Stability, Historical Intelligence |
| Recurrence | Reappearance or repeated presence of a structure, pattern, classification, or story across historical windows or fact sets. | Recurred structure | forecast return, cyclic guarantee | Persistence, Story Evolution, OBS-QUERY |
| Stability | Classification of whether observed structures remain steady, strengthen, weaken, drift, or destabilize across windows or comparisons. | Stability class | price stability prediction, risk forecast | Structural State, drift, historical/live comparison |
| Morphology | The shape or internal structure of sectors, subsectors, groups, or ecosystems, including coherent, fragmented, broad, fragile, dominant, or contrastive patterns. | Morphology class | topology prediction, market shape forecast | Ecology, Historical Intelligence, sector morphology |
| Ecology | Multi-window and cross-sectional context of market-structure observations, including window metrics, concentration, coverage, sector/subsector structure, and ecosystem characterization. | Market ecology, historical ecology | environment forecast, macro prediction | Morphology, Persistence, HIST-LONG |
| Historical Intelligence | The local, observational-only stack that converts completed historical ecology artifacts and fact rows into bounded evidence, structural findings, taxonomy weighting, narrative evolution, and ecosystem synthesis. | Hist Intel, HI | historical forecast, backtest recommendation | HIST-LONG, HIST-FACT, HIST-INTEL, DB-2 |
| Live Intelligence | The controlled live observation capability that ingests bounded current observations, accumulates them as DB-2 facts, and produces live structural-state snapshots. | Live Intel | live trading signal, real-time recommendation | OPS-LIVE, OPS-LIVE-1/2/3, Structural State |
| Queryable Intelligence | Existing facts and structural context exposed through retrieval-only OBS-QUERY interfaces as bounded questions, comparisons, validation scorecards, and consumption views. | Queryable intel | generated intelligence, synthetic recommendation | OBS-QUERY, DB-2, Consumption Products |
| Story | A deterministic presentation grouping or item derived from existing OBS-QUERY or Historical Intelligence artifacts, usually keyed by identifier, title, lifecycle, archetype, source, or classification fields. | Story item | generated narrative, investment thesis | Story Evolution, Daily Briefing, Story Detail |
| Story Evolution | A deterministic classification of how a story changes across available story history, limited to observed directions such as rising, stable, falling, reappearing, or unknown. | Evolution, story movement | forecast trajectory, expected trend | Story, Why Now, Consumption Products |
| Investigation Candidate | A ranked analyst-review item derived from existing comparison, query, or briefing artifacts, carrying priority, type, rationale, review questions, and evidence references. | Candidate, review candidate | trade idea, recommendation, action item | Investigation Queue, Why Now, Evidence |
| Why Now | A deterministic context phrase explaining why an existing story or candidate appears in the current presentation, based on story history, priority movement, confidence movement, first appearance, reappearance, persistence, or insufficient history. | Why-now context | catalyst prediction, timing recommendation | Story, Investigation Candidate, Daily Briefing |
| Quality Gate | A deterministic presentation filter that suppresses noisy, duplicate, low-value, evidence-only, internal, or overflowing display items without mutating source facts or artifacts. | Display quality gate | validation scorecard, data quality migration, fact filter | Consumption Products, Daily Briefing, Governance |
| DB-2 | The current SEFI fact-native observation-fact read model centered on `sefi_observation_facts`, with append-oriented bounded facts and lineage used by OBS-QUERY. | DB2, DB-2 read model | DB-1 when referring to current OBS-QUERY source of truth, warehouse, narrative store | Observation Fact, Fact Lineage, OBS-QUERY |
| OBS-QUERY | The retrieval-only interface over DB-2 observation facts that selects, groups, compares, validates, and prepares existing facts for consumption without creating facts or predictions. | OQ, OBS-QUERY-1/2/3/4/5 | query generator, prediction engine, recommendation engine | DB-2, Queryable Intelligence, Consumption Products |

## Terminology Conflicts Found

| Conflict | Where it appears | Risk | Preferred term |
|---|---|---|---|
| Evidence vs evidence table | Core concepts, data model notes, data model diagram | Readers may assume a dedicated DB-2 evidence table exists. | Use **Evidence Reference** when referring to payload-level/canonicalized evidence IDs; reserve **Evidence** for the conceptual support layer. |
| DB-1 vs DB-2 | DB-2 and data-model notes | Legacy migration comments can conflict with current architectural naming. | Use **DB-2** for the current observation-fact read model; mention DB-1 only as legacy terminology in comments/migrations. |
| Live Intelligence vs OPS-LIVE | Executive overview, system evolution, core concepts, OPS-LIVE notes | Capability and subsystem can be conflated. | Use **OPS-LIVE** for the subsystem and **Live Intelligence** for the capability/output category. |
| Queryable Intelligence vs OBS-QUERY | Executive overview, system evolution, core concepts, OBS-QUERY notes | Capability and implementation interface can be conflated. | Use **OBS-QUERY** for the subsystem/interface and **Queryable Intelligence** for the fact-backed capability. |
| Story Evolution vs narrative evolution | Historical Intelligence and Consumption Products | Historical narrative/regime outputs may be confused with presentation story history. | Use **Narrative Evolution** for HIST-INTEL historical outputs and **Story Evolution** for consumption-layer presentation changes. |
| Quality Gate vs validation | Consumption Products and Governance | Presentation suppression can be confused with OBS-QUERY-5 validation. | Use **Quality Gate** only for presentation filtering; use **Validation Scorecard** for OBS-QUERY-5. |
| Fact-like row vs persisted DB-2 fact | Historical Intelligence, OBS-QUERY, data model | Local fixtures or expanded historical rows may be mistaken for persisted rows. | Use **fact-like row** for local/unpersisted rows and **persisted DB-2 observation fact** for rows in `sefi_observation_facts`. |
| Source of truth vs local artifacts | DB-2, Consumption Products, Governance | Direct artifact consumption may appear to bypass DB-2 source-of-truth claims. | Use **DB-2 source of truth for OBS-QUERY fact retrieval**; call local artifacts **governed presentation inputs** when used by Consumption Products. |
| Structural State vs Structural Intelligence | System evolution, core concepts, OPS-LIVE notes | State output and broader architecture concept can blur. | Use **Structural State** for bounded classifications/snapshots and **Structural Intelligence** for the broader interpretive layer over facts. |
| Observation vs operational observation | Core concepts and OPS-LIVE notes | OPS-LIVE operational observations may be confused with normalized facts. | Use **Observation** or **operational observation** before OPS-LIVE-2; use **Observation Fact** only after normalization into fact shape. |

## Preferred Term Rules

1. Use **Observation** for bounded pre-normalization signals.
2. Use **Observation Fact** for normalized fact-shaped records; qualify as **persisted DB-2 observation fact** only when stored in `sefi_observation_facts`.
3. Use **Evidence Reference** for evidence IDs carried in payloads, canonicalization, row IDs, duplicate keys, or supporting ID lists.
4. Use **DB-2** for the current observation-fact read model.
5. Use **OBS-QUERY** for the retrieval-only subsystem.
6. Use **Queryable Intelligence** only for the capability produced by retrieval over existing facts.
7. Use **OPS-LIVE** for implementation phases; use **Live Intelligence** for the architectural capability.
8. Use **Quality Gate** only for consumption-layer display filtering.
9. Use **Validation Scorecard** for OBS-QUERY-5 validation outputs.
10. Use **Story** and **Story Evolution** only for deterministic presentation groupings, not for unsupported generated narratives.
