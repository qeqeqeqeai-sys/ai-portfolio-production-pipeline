# 07 — OBS-QUERY Architecture Source Notes

## Purpose
OBS-QUERY is the retrieval-only interface over DB-2 observation facts. It answers bounded analyst-oriented questions by selecting, grouping, comparing, and presenting existing facts without creating new facts or new intelligence.

Repository anchors: `observation_fact_retrieval.py`, `observation_intelligence_query.py`, `historical_live_comparison.py`, `analyst_consumption_views.py`, `obs_query_validation.py`.

## Architectural role
OBS-QUERY sits after DB-2 and Structural State Models and before Consumption Products. It is a layered read interface:
- OBS-QUERY-1: fact retrieval.
- OBS-QUERY-2: intelligence question retrieval.
- OBS-QUERY-3: historical vs live comparison.
- OBS-QUERY-4: consumption view generation.
- OBS-QUERY-5: deterministic validation.

## Inputs
- DB-2 rows from `sefi_observation_facts` or controlled local fact fixtures.
- Optional filters: symbol, taxonomy, source layer, snapshot date, evidence ID, historical/live source layers, comparison type, query type, view type, and limit.
- Controlled OBS-QUERY-5 fixtures shaped like DB-2 fact rows.

## Outputs
- Canonical fact retrieval envelopes.
- Ranked structure/result items for persisted, changed, recurred, dominant, weakened, and transitioned questions.
- Historical/live comparison result sets with classifications and deltas.
- Analyst consumption views with sections, supporting fact IDs, supporting evidence IDs, and governance certification.
- Validation scorecards with retrieval, comparison, consumption, traceability, and governance coverage.

## Major components
### OBS-QUERY-1
Retrieves bounded DB-2 facts, applies supported filters, reports unsupported filters, canonicalizes facts, and emits evidence references.

### OBS-QUERY-2
Answers typed intelligence questions over existing facts: `persisted`, `changed`, `recurred`, `dominant`, `weakened`, and `transitioned`. It ranks by deterministic score extractors and preserves supporting fact/evidence IDs.

### OBS-QUERY-3
Compares historical and live facts by identifier. Historical rows default to phase IDs beginning with `HIST` or `OPS-HIST`; live rows default to phase IDs beginning with `LIVE` or `OPS-LIVE`. Supported comparison types include baseline overlap, live anomalies, historical recurrence, persistent weakening live, weak strengthening live, and baseline deviation.

### OBS-QUERY-4
Generates analyst consumption views by composing OBS-QUERY-2 question results and OBS-QUERY-3 comparisons into predefined section blueprints: ecosystem briefing, change monitor, persistence monitor, anomaly monitor, and investigation queue.

### OBS-QUERY-5
Runs deterministic validation against controlled fact fixtures. It tests retrieval correctness, historical/live comparison, consumption view coverage, traceability, and governance compliance.

## Retrieval-only architecture
OBS-QUERY components operate on DB-2 rows or fixtures. Governance certifications disable provider API calls, DB writes, schema migrations, fact creation, prediction, recommendation, and market actions. OBS-QUERY-4 uses a fixed sentinel generation timestamp rather than wall-clock generation for deterministic output.

## Historical vs live comparison
OBS-QUERY-3 groups facts by deterministic identifiers, splits historical and live rows by source phase, calculates representative numeric values, derives deltas when both sides are numeric, classifies comparison outcomes, and carries separate historical/live supporting fact IDs plus evidence IDs.

## Consumption view generation
OBS-QUERY-4 uses static view blueprints. Query sections call OBS-QUERY-2; comparison sections call OBS-QUERY-3; queue sections aggregate selected comparison types into deterministic investigation candidates. Each section carries items, supporting facts, supporting evidence IDs, and deduplicated evidence rows.

## Data flow
DB-2 facts → OBS-QUERY-1 canonical retrieval → OBS-QUERY-2 typed retrieval questions → OBS-QUERY-3 historical/live comparison → OBS-QUERY-4 consumption views → OBS-QUERY-5 validation → Daily Briefing and other presentation consumers.

## Governance boundaries
- Read-only retrieval from `sefi_observation_facts` or local controlled fixtures.
- No fact creation or mutation.
- No external provider calls.
- No schema migrations.
- No predictions, recommendations, or market actions.
- Output must retain traceability to fact IDs and evidence IDs.

## Downstream consumers
- Daily Briefing adapter and Streamlit application.
- Investigation Queue workflow.
- Story Detail evidence drill-down.
- Validation and test suites.
- Future whitepaper sections for Historical Intelligence, OPS-LIVE, and Consumption Products.

## Important implementation details
- Hard/effective limits bound query results.
- Local fixture mode allows deterministic validation without database writes.
- Ranking uses deterministic sort keys: score, classification/type, identifier, source fields.
- Unsupported filters are surfaced rather than silently synthesized.
- Query outputs duplicate `query_parameters`/`parameters` where needed for compatibility.

## Glossary of subsystem-specific terms
- **OBS-QUERY-1**: Observation fact retrieval layer.
- **OBS-QUERY-2**: Typed intelligence question retrieval layer.
- **OBS-QUERY-3**: Historical vs live comparison layer.
- **OBS-QUERY-4**: Analyst consumption view layer.
- **OBS-QUERY-5**: Validation harness and scorecard.
- **Retrieval-only**: Existing facts are selected and arranged; no new facts or predictions are created.
- **Supporting fact IDs**: DB-2 fact identifiers retained for drill-down.
- **Supporting evidence IDs**: Evidence identifiers carried from payloads or row metadata.
