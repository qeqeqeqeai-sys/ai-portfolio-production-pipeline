# 01 — Executive Overview

## What SEFI is
SEFI is a fact-native market-intelligence architecture that converts bounded historical and live observations into traceable observation facts, structural context, queryable intelligence, and presentation-only analyst views.

Its current source-pack architecture is organized around:

1. **Historical Intelligence** over completed local ecology artifacts.
2. **OPS-LIVE** controlled live observation ingestion, fact accumulation, and structural-state snapshotting.
3. **DB-2** as the central append-oriented observation-fact read model.
4. **OBS-QUERY** as a retrieval-only interface over DB-2 facts.
5. **Consumption Products** as presentation-only views for analysts.
6. **Governance** embedded across emission, retrieval, comparison, and presentation boundaries.

## Why it exists
SEFI exists to make market-structure observations reviewable, comparable, and consumable without converting them into forecasts, trading instructions, or opaque generated narratives. The architecture emphasizes observable evidence, deterministic transformations, bounded payloads, and lineage preservation from source phase to analyst presentation.

## Problem it solves
The repository addresses a recurring systems problem: raw or artifact-level observations are difficult to audit, compare across time, and safely present to analysts unless they are normalized into stable facts with clear lineage.

SEFI solves this by separating:

- **Observation capture** from fact persistence.
- **Fact persistence** from intelligence retrieval.
- **Historical/live comparison** from prediction.
- **Analyst presentation** from new intelligence generation.

This separation lets downstream consumers ask bounded questions about persisted, changed, recurring, dominant, weakened, or transitioned structures while retaining fact IDs, evidence IDs, artifact IDs, run IDs, source phases, and governance context.

## Architectural principles
- **Fact-native read model**: DB-2 centers the architecture on `sefi_observation_facts`, not on generated prose or unbounded artifacts.
- **Bounded transformations**: payloads, query limits, section caps, fixture validation, and source-universe controls constrain each layer.
- **Explicit lineage**: phase, artifact, run, entity, metric, window, payload, evidence, and duplicate-prevention identifiers remain available downstream.
- **Layer separation**: ingestion, accumulation, structural-state synthesis, retrieval, comparison, validation, and presentation are distinct responsibilities.
- **Deterministic behavior**: sorting, ranking, duplicate prevention, quality gates, and validation fixtures favor reproducible outputs.
- **Read-only query and presentation**: OBS-QUERY and Consumption Products arrange existing facts and artifacts without provider calls, schema changes, or database writes.
- **Fail-closed posture**: missing inputs, unsupported filters, disabled write gates, invalid payloads, or insufficient facts result in bounded summaries or insufficient-data states rather than silent synthesis.

## Fact-native intelligence philosophy
SEFI treats intelligence as structured interpretation over retained facts, not as unsupported generation. Historical and live layers may classify persistence, recurrence, stability, morphology, ecology, drift, health, and structural state, but those classifications must remain tied to source facts, evidence identifiers, artifacts, runs, and governed source phases.

In this architecture, a useful intelligence output is one that can answer:

- Which observation facts support it?
- Which evidence identifiers and source phases are attached?
- Which historical or live layer produced the source signal?
- Which governance boundary prevents it from becoming prediction, recommendation, or market action?

## Current architecture summary
The current architecture flows from market and historical inputs into bounded observations, normalized observation facts, DB-2 accumulation, historical intelligence, live structural state, OBS-QUERY retrieval/comparison, and presentation-only consumption products.

- **Historical Intelligence** converts completed local ecology artifacts into fact/evidence rows, structural findings, narrative/evolution signals, taxonomy weighting, and ecosystem synthesis.
- **OPS-LIVE-1** produces bounded live operational observations over a controlled universe.
- **OPS-LIVE-2** normalizes live observations into DB-2 observation facts behind dry-run and explicit write gates.
- **OPS-LIVE-3** reads accumulated facts and synthesizes bounded structural-state snapshots.
- **DB-2** stores append-oriented observation facts with lineage and duplicate-prevention keys.
- **OBS-QUERY** retrieves, groups, compares, and presents existing DB-2 facts through typed questions, historical/live comparisons, and validation scorecards.
- **Consumption Products** adapt existing OBS-QUERY and historical-intelligence artifacts into Daily Briefing, Story Evolution, Investigation Queue, Story Detail, Why Now, and Quality Gate views.

## Governance philosophy
SEFI governance is embedded in the architecture rather than delegated to a final review step. The current repository evidence supports the following boundaries:

- No forecasting, prediction, trading, portfolio recommendation, or market-action behavior in the documented layers.
- No provider calls in DB-2 fact emission, OBS-QUERY retrieval, or Consumption Product presentation.
- No schema migrations, database writes, or fact creation in OBS-QUERY or presentation layers.
- DB-2 writes require explicit enablement, non-dry execution, valid context, bounded payloads, duplicate-prevention keys, and a supplied database client.
- Evidence traceability is preserved through supporting fact IDs, supporting evidence IDs, artifact IDs, run IDs, source phases, and source-run fields.
- Unsupported filters and insufficient data are surfaced rather than hidden by synthetic substitutes.

## Architectural ambiguities
- Evidence identifiers are currently carried in payloads or canonicalized from row identifiers; the source pack does not document a dedicated evidence table.
- Source-universe DB loading has a validated configuration fallback, so live-ingestion reviewers must distinguish DB-sourced universe rows from fallback telemetry.
- The current documentation describes DB-2 as the central observation-fact read model while noting legacy DB-1 historical read-model terminology in migration comments.
