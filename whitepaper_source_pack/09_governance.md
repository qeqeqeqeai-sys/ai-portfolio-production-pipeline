# 09 — Governance Source Notes

## Purpose
This document captures the governance posture shared by DB-2, OBS-QUERY, and Consumption Products: deterministic, evidence-traceable, retrieval-only, no-prediction/no-recommendation, and fact-native intelligence.

Repository anchors: `fact_emitter.py`, `ops_live2_observation_fact_accumulation.py`, `observation_fact_retrieval.py`, `observation_intelligence_query.py`, `historical_live_comparison.py`, `analyst_consumption_views.py`, `obs_query_validation.py`, `daily_briefing/adapter.py`.

## Architectural role
Governance is not a separate output layer; it is embedded in construction, retrieval, validation, and presentation. It constrains what each subsystem may do and makes downstream outputs auditable back to DB-2 facts.

## Inputs
- Existing observations and DB-2 fact rows.
- Explicit emission contexts and dry-run/write gates.
- Query parameters and deterministic view blueprints.
- Controlled validation fixtures.
- Existing local artifacts for presentation.

## Outputs
- Governance certification fields on OBS-QUERY outputs.
- Governance review fields on OPS-LIVE-2 accumulation reports.
- Validation scorecards for retrieval, comparison, consumption, traceability, and governance.
- Presentation-only view models with bounded evidence drill-down.

## Major components
- **Deterministic emission controls**: stable normalization, bounded payloads, duplicate prevention keys, and dry-run defaults.
- **Retrieval certifications**: explicit flags disabling synthesis, writes, schema migrations, provider calls, predictions, recommendations, and market actions.
- **Traceability validation**: OBS-QUERY-5 checks that non-empty outputs retain fact/evidence drill-down and match fixture IDs.
- **Presentation guardrails**: Daily Briefing adapter selects and labels existing artifacts but does not persist derived fields or generate new intelligence.

## Deterministic design
Determinism appears in stable string normalization, sorted payload keys, SHA-256 duplicate keys, bounded limits, deterministic sort orders, fixed view blueprints, fixed validation fixtures, and fixed sentinel generation timestamps for OBS-QUERY-4.

## Evidence traceability
Traceability is maintained through `fact_id`, `evidence_id`, `artifact_id`, `run_id`, source phases, historical/live supporting fact IDs, and evidence drill-down. OBS-QUERY-5 explicitly tests the chain from view/result to fact to evidence.

## Retrieval-only boundaries
OBS-QUERY layers read from DB-2 or fixtures. They can filter, rank, group, compare, and assemble views, but cannot call providers, write to the database, create facts, mutate schema, or synthesize new intelligence.

## No prediction boundaries
Governance certifications disable prediction fields across OBS-QUERY. OPS-LIVE-2 governance review also disables prediction behavior. Consumption documentation and adapter comments prohibit forecasting or prediction/trading language.

## No recommendation boundaries
OBS-QUERY certifications disable recommendations and market actions. Consumption products may provide analyst review questions, but those are not investment, portfolio, trading, or action recommendations; they are presentation prompts tied to existing evidence.

## Fact-native intelligence philosophy
The current architecture privileges facts over generated narrative. Intelligence products are downstream arrangements of observation facts and evidence references. When information is unavailable or unsupported, the system exposes insufficiency or unsupported filters rather than inventing fields.

## Data flow
Governed observations → deterministic fact emission → DB-2 source-of-truth facts → retrieval-only OBS-QUERY → traceable comparison/view outputs → presentation-only Daily Briefing / Investigation Queue → analyst evidence drill-down.

## Governance boundaries
- Fail closed on invalid fact rows or payloads.
- Dry-run default for emission.
- Explicit write gates only.
- No provider calls inside DB-2/OBS-QUERY/consumption paths.
- No DB writes or schema changes in OBS-QUERY and consumption layers.
- No prediction, recommendation, trading, or market-action language.
- Preserve lineage and evidence IDs in downstream views.

## Downstream consumers
- Whitepaper sections that need governance architecture details.
- Validation reviewers.
- Analysts consuming Daily Briefing and Story Detail evidence drill-downs.
- Developers extending OBS-QUERY or consumption views under the same boundaries.

## Important implementation details
- Unsupported OBS-QUERY filters are explicitly listed with reasons instead of inferred.
- OBS-QUERY-5 has five validation categories: retrieval correctness, historical/live validation, consumption view validation, traceability validation, and governance validation.
- Daily Briefing quality gate is explicitly display-only and hides suppressed item details.
- Streamlit app caption declares read-only behavior, no schema changes, no writes, and no new intelligence generation.

## Glossary of subsystem-specific terms
- **Governance certification**: Output-level declaration of disabled capabilities and source-of-truth constraints.
- **Dry-run default**: Safe emission mode that builds rows and summaries without persistence.
- **Fail closed**: Reject invalid context, payloads, metric values, or duplicate keys rather than partially emitting.
- **Evidence traceability**: Ability to drill from presentation item to fact and evidence identifiers.
- **No prediction boundary**: Prohibition on forecasting or predictive outputs.
- **No recommendation boundary**: Prohibition on investment, trading, portfolio, or market-action recommendations.
- **Fact-native intelligence**: Architecture in which downstream intelligence is retrieval and arrangement of stored facts, not generation of unsupported claims.
