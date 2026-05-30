# 02 — System Evolution

## Scope
This document describes the current architecture as an evidence-supported evolution of layers. It does not assert a chronological project history beyond transitions documented in the source pack.

The architectural sequence is:

Observation
↓
Fact
↓
Historical Intelligence
↓
Live Intelligence
↓
Structural Intelligence
↓
Query Layer
↓
Consumption Products

## 1. Observation

### Why the layer exists
Observations are the bounded raw material of SEFI. Historical layers consume completed local ecology artifacts. Live layers consume controlled operational observations over a governed universe. This layer exists so the system can capture market-structure signals before they are normalized into a common fact shape.

### Current implementation evidence
- Historical observation sources include HIST-LONG ecology, temporal-delta, cross-sectional, intra-group, persistence, and drift artifacts.
- OPS-LIVE-1 produces bounded live operational observations, validates the source universe, and avoids DB-2 fact writes directly.
- Observation payloads carry metadata such as observed time, source phase, source run, identifiers, classifications, and evidence identifiers.

### Transition enabled
Observation creates the input substrate for fact emission but does not itself guarantee stable lineage, duplicate handling, or queryability.

## 2. Fact

### Why the layer exists
The Fact layer exists to normalize observations into stable, bounded, lineaged rows that downstream systems can retrieve and compare. DB-2's central table, `sefi_observation_facts`, provides the common shape for source phase, entity, metric, value, window, payload, artifact, run, and duplicate-prevention lineage.

### Current implementation evidence
- DB-2 fact emission validates context, required fields, payload shape/size, numeric or null metric values, and deterministic duplicate-prevention keys.
- OPS-LIVE-2 emits live observations as DB-2 observation facts only when write gates are explicitly enabled and non-dry execution has a database client.
- Retrieval canonicalizes fact IDs, evidence IDs, artifact IDs, run IDs, taxonomy fields, and payloads for downstream use.

### Transition enabled
Fact normalization turns heterogeneous observations into append-oriented evidence units that can support historical intelligence, live state synthesis, OBS-QUERY retrieval, and presentation drill-downs.

## 3. Historical Intelligence

### Why the layer exists
Historical Intelligence exists to interpret completed historical ecology artifacts and fact rows into reviewable structure: persistence, recurrence, stability, morphology, ecology, drift, taxonomy weighting, narrative evolution, and ecosystem synthesis.

### Current implementation evidence
- HIST-LONG layers establish multi-window ecology, temporal sensitivity, cross-sectional differentiation, intra-group structural contrast, persistence, and stability drift.
- HIST-FACT layers create bounded observation facts and regime evidence from historical artifacts.
- HIST-INTEL layers group facts into structural findings, fact-native findings, taxonomy weights, narrative/evolution outputs, and ecosystem synthesis.

### Transition enabled
Historical Intelligence supplies baseline context and historical structure that can later be compared with live facts without becoming a forecast.

## 4. Live Intelligence

### Why the layer exists
Live Intelligence exists to bring current controlled observations into the same fact-native architecture used for historical context. It separates live ingestion from persistence and structural-state synthesis.

### Current implementation evidence
- OPS-LIVE-1 handles controlled live ecosystem ingestion and universe validation.
- OPS-LIVE-2 performs controlled live observation fact accumulation into DB-2 with dry-run defaults and explicit write gates.
- OPS-LIVE-3 reads accumulated facts and creates bounded live structural-state snapshots.

### Transition enabled
Live Intelligence lets the system compare current observed facts against historical baselines and live health/state classes while preserving the no-prediction boundary.

## 5. Structural Intelligence

### Why the layer exists
Structural Intelligence exists because analysts need more than isolated facts: they need evidence-backed state, comparison, persistence, change, recurrence, dominance, weakening, and transition context.

### Current implementation evidence
- Historical layers classify persistence, recurrence, stability, morphology, ecology, and structural evolution.
- OPS-LIVE-3 classifies live health dimensions such as ingestion completeness, provider health, weakness pressure, replay pressure, contradiction pressure, concentration pressure, and overall live health.
- OBS-QUERY-2 and OBS-QUERY-3 expose typed questions and historical/live comparisons over existing facts.

### Transition enabled
Structural Intelligence creates the conceptual bridge between persisted facts and analyst questions while retaining source fact and evidence references.

## 6. Query Layer

### Why the layer exists
The Query Layer exists to make DB-2 and structural outputs accessible without mutating them. OBS-QUERY provides retrieval-only access, typed intelligence questions, historical/live comparisons, consumption-view generation, and validation.

### Current implementation evidence
- OBS-QUERY-1 retrieves and canonicalizes DB-2 facts.
- OBS-QUERY-2 answers typed questions for persisted, changed, recurred, dominant, weakened, and transitioned structures.
- OBS-QUERY-3 compares historical and live facts by deterministic identifiers.
- OBS-QUERY-4 composes analyst consumption views from query and comparison sections.
- OBS-QUERY-5 validates retrieval, comparison, consumption, traceability, and governance behavior.

### Transition enabled
The Query Layer converts fact-native storage into bounded, repeatable analyst-facing result sets without provider calls, writes, fact creation, prediction, recommendation, or market action.

## 7. Consumption Products

### Why the layer exists
Consumption Products exist to present existing OBS-QUERY and historical-intelligence outputs in analyst-usable forms while preserving the presentation-only boundary.

### Current implementation evidence
- The Daily Briefing adapter normalizes existing artifacts into briefing cards, story evolution highlights, investigation candidates, story details, quality metadata, and evidence drill-downs.
- Story Evolution uses deterministic story histories and bounded evolution directions.
- Investigation Queue ranks candidates deterministically and provides analyst review questions tied to evidence rather than recommendations.
- Quality Gate suppresses display noise without mutating source data.

### Transition enabled
Consumption Products make the fact/query architecture reviewable by technical reviewers, supervisors, research directors, and analysts without adding unsupported intelligence claims.

## Current end-to-end transition
The current architecture can be summarized as:

Bounded observations become normalized facts; facts accumulate in DB-2; historical and live layers derive structural context from existing artifacts and facts; OBS-QUERY retrieves and compares existing facts; Consumption Products present selected, traceable views with quality gates and evidence drill-downs.

## Architectural ambiguities
- The source pack supports the layer sequence but does not fully establish a chronological build history for every layer.
- Historical read-model and DB-2 terminology overlap in the data model documentation, especially where migration comments reference DB-1 while current architecture centers DB-2 observation facts.
- Evidence IDs are traceable through payloads and canonicalization but are not documented as a dedicated persisted evidence table.
