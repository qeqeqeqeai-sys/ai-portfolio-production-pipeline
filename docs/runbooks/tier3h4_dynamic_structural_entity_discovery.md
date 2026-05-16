# Tier 3H.4A — Dynamic Structural Entity Discovery (Advisory Scaffold)

## Purpose
Tier 3H.4A introduces a deterministic scaffold for dynamic structural entity discovery records. It is a staging layer for future evidence enrichment and review workflow, without any monitored-universe promotion.

## Advisory-only guarantee
- Writes only to `public.tier3h_dynamic_entity_discovery`.
- Never writes to monitored-universe tables.
- No buy/sell recommendations.
- No autonomous trading actions.
- `llm_used` is hard-locked to `false` in this phase.

## What is implemented now
- Deterministic upstream context loader from Tier 3H and structural propagation sources (if available).
- Safe deterministic fallback seeds when upstream tables are unavailable or empty.
- Deterministic mock evidence generation (no external retrieval APIs).
- Deterministic confidence scoring with auditable component scores.
- Advisory-only persistence with idempotent daily upsert key.
- Structured logs and summary/validation artifacts.
- GitHub Actions workflow for manual and scheduled runs.

## What is intentionally not implemented yet
- 3H.4B Tavily evidence collection.
- 3H.4D OpenAI / LLM classification.
- Monitored-universe auto-promotion.
- Portfolio/trading actions.

## Table schema
SQL migration: `sql/tier3h_dynamic_entity_discovery.sql`.

Key fields:
- idempotency: `(run_date_sgt, theme_name, candidate_asset_id, discovery_method)`
- evidence payload: `evidence_sources`, `evidence_count`
- scoring fields: `source_quality_score`, `thematic_relevance_score`, `entity_resolution_score`, `cross_source_score`, `candidate_confidence_score`
- controls: `candidate_confidence_band`, `advisory_status`, `rejection_reason`, `llm_used`

## Scoring logic
`candidate_confidence_score` (0..100) is deterministic weighted sum:
- evidence_count_score: 30%
- thematic_relevance_score: 25%
- source_quality_score: 20%
- entity_resolution_score: 15%
- cross_source_score: 10%

## Confidence bands
- `>= 80`: `high_confidence`
- `>= 60 and < 80`: `medium_confidence`
- `>= 40 and < 60`: `low_confidence`
- `< 40`: `rejected_or_noise`

Advisory status mapping:
- high/medium/low → `advisory_review`
- rejected_or_noise → `advisory_rejected`

## GitHub Actions usage
Workflow: `.github/workflows/tier3h4_dynamic_entity_discovery.yml`
- `workflow_dispatch` for manual run.
- daily schedule for drift-free advisory refresh.
- uploads summary/validation/context artifacts under `logs/`.

## Rollout risks
- Upstream context schema drift may reduce seed quality (mitigated by soft fallback path).
- Confidence weights are deterministic but not calibrated to production outcomes yet.
- Mock evidence is scaffold-only and should not be interpreted as external corroboration.

## Future phases
- **3H.4B:** Tavily evidence collection.
- **3H.4C:** Entity resolution hardening.
- **3H.4D:** LLM classification with strict JSON + evidence lock.
- **3H.4E:** Confidence calibration + suppression rules.
- **3H.4F:** Human-review promotion workflow.
