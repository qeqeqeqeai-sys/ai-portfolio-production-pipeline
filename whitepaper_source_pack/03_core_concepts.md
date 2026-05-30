# 03 — Core Concepts

## Observation
- **Definition**: A bounded historical or live source signal captured before normalization into the DB-2 observation-fact shape.
- **Purpose**: Preserve source-layer signal and metadata for later fact emission or structural analysis.
- **Producer**: HIST-LONG historical artifact layers; OPS-LIVE-1 controlled live ingestion; bounded local fixtures.
- **Consumer**: HIST-FACT layers, DB-2 fact emitter, OPS-LIVE-2, OPS-LIVE-3, Historical Intelligence.

## Observation Fact
- **Definition**: A normalized DB-2 row or fact-like row representing an observation with phase, entity, metric, value, window, payload, artifact, run, and duplicate-prevention lineage.
- **Purpose**: Make observations stable, retrievable, comparable, and evidence-traceable.
- **Producer**: `fact_emitter.py`, OPS-LIVE-2, HIST-FACT layers, historical fact-expansion layers.
- **Consumer**: DB-2, OBS-QUERY-1, OBS-QUERY-2, OBS-QUERY-3, OPS-LIVE-3, Consumption Products.

## Evidence
- **Definition**: The source support associated with a fact or view item, commonly carried through `payload_jsonb.evidence_id`, row IDs, duplicate-prevention keys, or supporting Evidence Reference identifier lists.
- **Purpose**: Enable drill-down from analyst-facing outputs back to the source observations or facts that support them.
- **Producer**: Historical fact/evidence expansion, DB-2 payloads, OBS-QUERY canonicalization, consumption view builders.
- **Consumer**: OBS-QUERY, Daily Briefing, Story Detail, governance review, analyst Evidence Reference drill-down.

## Fact Lineage
- **Definition**: The set of identifiers and metadata that bind a fact to its producing phase, artifact, run, source payload, entity, metric, window, and duplicate-prevention identity.
- **Purpose**: Preserve auditability and prevent unsupported synthesis or anonymous findings.
- **Producer**: DB-2 fact emitter, OPS-LIVE-2 parent registry emission, historical loaders and fact expanders.
- **Consumer**: DB-2 retrieval, OBS-QUERY canonicalization, historical/live comparison, Consumption Products, governance validation.

## Structural State
- **Definition**: A bounded classification of current or historical system condition derived from existing facts, such as live health classes, pressure dimensions, coverage summaries, or historical structural classifications.
- **Purpose**: Summarize fact sets into reviewable state without creating forecasts or trading actions.
- **Producer**: OPS-LIVE-3, HIST-INTEL layers, historical morphology/persistence/drift layers.
- **Consumer**: OBS-QUERY, live monitoring surfaces, historical/live comparison, analyst consumption views.

## Persistence
- **Definition**: The degree to which a structure or signal remains present across historical windows or repeated fact sets.
- **Purpose**: Distinguish durable structures from one-off observations.
- **Producer**: HIST-LONG-8, HIST-LONG-9, HIST-INTEL layers, OBS-QUERY typed retrieval over existing facts.
- **Consumer**: Historical Intelligence, OBS-QUERY persisted/recurred questions, persistence watchlists, Daily Briefing.

## Stability
- **Definition**: A classification of whether observed structures remain steady, strengthen, weaken, drift, or destabilize across windows or comparisons.
- **Purpose**: Support structural review of continuity and change without predictive claims.
- **Producer**: HIST-LONG-5B, HIST-LONG-6, HIST-LONG-8, HIST-LONG-9, OPS-LIVE-3, historical/live comparison.
- **Consumer**: Historical Intelligence, Structural State snapshots, OBS-QUERY comparisons, Consumption Products.

## Recurrence
- **Definition**: Reappearance or repeated presence of a structure, pattern, classification, or story across historical windows or fact sets.
- **Purpose**: Identify structures that return or repeat and therefore merit retrieval and analyst review.
- **Producer**: HIST-LONG-8, HIST-INTEL Narrative Evolution layers, OBS-QUERY recurred question handling, Story Evolution.
- **Consumer**: OBS-QUERY, Daily Briefing, Story Evolution Highlights, Investigation Queue.

## Morphology
- **Definition**: The shape or internal structure of sectors, subsectors, groups, or ecosystems, including coherent, fragmented, broad, fragile, dominant, or contrastive patterns.
- **Purpose**: Describe how market-structure signals are distributed within and across groups.
- **Producer**: HIST-LONG-7, sector morphology read-model loaders, HIST-INTEL ecosystem synthesis.
- **Consumer**: Historical Intelligence, OBS-QUERY structural questions, Consumption Products.

## Ecology
- **Definition**: The multi-window and cross-sectional context of market-structure observations, including window metrics, concentration, coverage, sector/subsector structure, and ecosystem characterization.
- **Purpose**: Provide the historical and structural substrate from which persistence, morphology, stability, and drift are derived.
- **Producer**: HIST-LONG-4, HIST-LONG-6, history read-model loader, historical ecology artifacts.
- **Consumer**: HIST-LONG-5B/6/7/8/9, HIST-FACT, HIST-INTEL, DB-2, OBS-QUERY.

## Historical Intelligence
- **Definition**: The local, observational-only stack that converts completed historical ecology artifacts and fact rows into bounded evidence, structural findings, taxonomy weighting, Narrative Evolution, and ecosystem synthesis.
- **Purpose**: Establish traceable historical context for structural review and later historical/live comparison.
- **Producer**: HIST-LONG, HIST-FACT, and HIST-INTEL layers.
- **Consumer**: DB-2, OBS-QUERY, Consumption Products, architecture reviewers.

## Live Intelligence
- **Definition**: The controlled live observation path that ingests bounded current observations, accumulates them as DB-2 facts, and produces live structural-state snapshots.
- **Purpose**: Bring current observations into the same fact-native architecture as historical context.
- **Producer**: OPS-LIVE-1, OPS-LIVE-2, OPS-LIVE-3.
- **Consumer**: DB-2, OBS-QUERY, historical/live comparison, live monitoring and consumption views.

## Queryable Intelligence
- **Definition**: Existing facts and structural context exposed through retrieval-only OBS-QUERY interfaces as bounded questions, comparisons, Validation Scorecard outputs, and consumption views.
- **Purpose**: Let analysts and reviewers inspect persisted, changed, recurred, dominant, weakened, transitioned, anomalous, or deviating structures without creating new facts.
- **Producer**: OBS-QUERY-1 through OBS-QUERY-5.
- **Consumer**: Daily Briefing adapter, Streamlit presentation pages, Investigation Queue, Story Detail, validation suites.

## Story
- **Definition**: A deterministic presentation grouping or item derived from existing OBS-QUERY or historical-intelligence artifacts, usually keyed by identifier, title, lifecycle, archetype, source, or classification fields.
- **Purpose**: Present related evidence-backed developments in a form analysts can review.
- **Producer**: Daily Briefing adapter and Consumption Product logic.
- **Consumer**: Daily Briefing, Story Detail, Story Evolution Highlights, analyst reviewers.

## Story Evolution
- **Definition**: A deterministic classification of how a story changes across available story history, limited to directions such as rising, stable, falling, reappearing, or unknown.
- **Purpose**: Explain observed presentation change without forecasting future movement.
- **Producer**: Consumption Product story-history and evolution logic.
- **Consumer**: Daily Briefing, Story Evolution Highlights, Story Detail.

## Investigation Candidate
- **Definition**: A ranked analyst-review item derived from existing comparison, query, or briefing artifacts, carrying priority, type, rationale, review questions, and Evidence References.
- **Purpose**: Focus analyst attention on traceable structures that may warrant review, without recommending market action.
- **Producer**: OBS-QUERY-4 investigation queue sections and Daily Briefing adapter ranking logic.
- **Consumer**: Investigation Queue, Daily Briefing, Story Detail, analysts.

## Why Now
- **Definition**: A deterministic context phrase explaining why an existing story or candidate appears in the current presentation, based on story history, priority movement, confidence movement, first appearance, reappearance, persistence, or insufficient history.
- **Purpose**: Give analysts concise timing context while staying grounded in available artifacts.
- **Producer**: Consumption Product adapter templates.
- **Consumer**: Daily Briefing, Investigation Queue, Story Detail.

## Quality Gate
- **Definition**: A deterministic presentation filter that suppresses noisy, duplicate, low-value, evidence-only, internal, or overflowing display items without mutating source facts or artifacts.
- **Purpose**: Improve analyst readability while preserving aggregate quality metadata and evidence boundaries.
- **Producer**: Daily Briefing adapter and Consumption Product presentation logic.
- **Consumer**: Daily Briefing view model, Streamlit presentation pages, analyst reviewers.
