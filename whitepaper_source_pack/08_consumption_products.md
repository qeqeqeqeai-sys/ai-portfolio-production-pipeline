# 08 — Consumption Products Source Notes

## Purpose
Consumption Products are presentation-only views over existing SEFI intelligence outputs. They make OBS-QUERY results usable for analysts without changing DB-2, emitting new facts, calling providers, or introducing prediction/recommendation language.

Repository anchors: `transmission_layers/daily_briefing/adapter.py`, `apps/sefi_daily_briefing.py`, `transmission_layers/history_read_model/analyst_consumption_views.py`, `README_DEMO.md`.

## Architectural role
The consumption layer sits after OBS-QUERY. OBS-QUERY-4 creates structured analyst views; the Daily Briefing adapter normalizes existing OBS-QUERY/HIST-INTEL artifacts into briefing cards, investigation candidates, story details, quality metadata, and Evidence Reference drill-downs.

## Inputs
- OBS-QUERY-4 ecosystem briefing and investigation queue artifacts.
- OBS-QUERY-3 historical/live comparison artifacts.
- HIST-INTEL style ecosystem synthesis artifacts when available.
- Selected briefing date.
- Existing section items with identifiers, classification, ranking metric, deltas, source phases, supporting fact IDs, and supporting Evidence Reference identifiers.

## Outputs
- Daily Briefing view model.
- Story Evolution highlights.
- Deterministic Investigation Queue.
- Story Detail model with Why Now context and Evidence Reference drill-down.
- Briefing Quality Gate presentation summary counts.
- Streamlit presentation pages: Daily Briefing, Investigation Queue, Story Detail.

## Major components
### Daily Briefing
Shows briefing date, attention level, quality status, confidence labels, major developments, story evolution highlights, investigation candidates, historical/live deviation highlights, emerging themes, and persistence watchlist.

### Story Evolution
Builds deterministic story histories from existing artifact fields only. Stable `story_key` values are based on identifiers/titles where possible, with lifecycle/archetype/source/classification fallback. Evolution directions are limited to `rising`, `stable`, `falling`, `reappearing`, and `unknown`.

### Investigation Queue
Ranks existing investigation candidates deterministically by priority, investigation type, metric, title, and ID. Items include investigation type, lifecycle state, narrative archetype, priority, why it appears, Why Now text, analyst value, recommended questions, and Evidence References.

### Why Now
Uses deterministic templates from story history: insufficient prior history, first appearance after absence, priority increased, confidence improved, priority/lifecycle weakened, no material change, or persistence continuing.

### Quality Gate
Suppresses display noise using deterministic presentation filters: missing meaningful title/identifier, evidence-only items, internal governance/pipeline/validation artifacts, duplicates, low confidence when stronger alternatives exist, low priority investigation items when higher-priority items exist, and section overflow.

## Data flow
OBS-QUERY artifacts → adapter loading → section extraction → quality gate → story history/evolution classification → investigation ranking → Daily Briefing view model → Streamlit presentation pages → Evidence Reference drill-down.

## Governance boundaries
- Presentation-only and read-only.
- No schema migrations, tables, Supabase writes, pipeline alterations, external API calls, new intelligence generation, forecasting, prediction, or trading language.
- Suppressed item details are not rendered; only aggregate quality counts appear.
- Top-level briefing cards omit raw Evidence Reference identifiers; Story Detail preserves drill-down IDs.

## Downstream consumers
- Analysts using Streamlit Daily Briefing.
- Story Detail / Evidence Reference drill-down reviewers.
- Later whitepaper authors needing repository-grounded source material.
- Potential reporting surfaces that consume the same presentation view model.

## Important implementation details
- Default artifact paths include artifacts/outputs/reports locations, but the adapter treats them as existing local inputs and does not write to them.
- Section caps are fixed: 5 major developments, 7 investigation candidates, 5 historical/live deviations, 5 emerging themes, 5 persistence watchlist items, and 5 evolution highlights per group.
- Empty/thin/strong/noisy quality statuses are deterministic.
- The Streamlit app announces the read-only MVP boundary in its caption.
- Evidence drill-down lists supporting fact IDs, supporting Evidence Reference identifiers, historical/live supporting fact IDs, and source phases.

## Glossary of subsystem-specific terms
- **Daily Briefing**: Analyst-facing presentation model over existing SEFI artifacts.
- **Story Evolution highlights**: Capped groups of rising/reappearing/falling/stable stories derived from deterministic history comparison.
- **Investigation Queue**: Ranked presentation list for analyst review.
- **Why Now**: Deterministic context phrase explaining current story prominence from existing history.
- **Quality Gate**: Presentation filter that suppresses noisy or low-value display items without mutating source data.
- **Presentation-only boundary**: Constraint that the layer may format and select existing information but may not create facts, predictions, recommendations, or persistence changes.
