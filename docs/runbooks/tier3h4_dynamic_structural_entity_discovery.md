# Tier 3H.4B — Dynamic Structural Entity Discovery (Advisory Scaffold)

## Purpose
Tier 3H.4B extends Tier 3H.4A with deterministic Tavily evidence collection and evidence-aware scoring while preserving advisory-only isolation.

## Guardrails
- Tavily is **evidence collection only**.
- No OpenAI/LLM classification in 3H.4B.
- No monitored-universe writes.
- No buy/sell recommendations or autonomous trading actions.

## Tables
- Candidate advisory table: `public.tier3h_dynamic_entity_discovery`.
- New raw evidence table: `public.tier3h_dynamic_entity_evidence`.
- Evidence idempotency key: `(run_date_sgt, theme_name, query_text, source_url)`.

## 3H.4B logic
1. Load deterministic upstream seed context from Tier 3H candidates + structural propagation.
2. Deterministically generate query templates per theme.
3. If `TAVILY_API_KEY` exists and `TIER3H4_TAVILY_ENABLED=true`, collect Tavily evidence.
4. If unavailable, safely fallback to deterministic mock evidence.
5. Normalize evidence (domain/snippet, dedupe by idempotency key).
6. Score evidence quality deterministically.
7. Persist raw evidence rows and advisory candidates.
8. Apply deterministic suppression rules for weak/noisy candidates (without deleting evidence audit trail).

## Query generation
Deterministic templates:
- `{theme_label} public companies`
- `{theme_label} listed companies`
- `{theme_label} infrastructure suppliers`
- `{theme_label} earnings transcript companies`
- `{theme_label} ETF holdings companies`

## Evidence quality scoring
Deterministic components include:
- source domain tier
- thematic keyword overlap
- source rank influence
- snippet specificity
- duplicate/weakness penalties via suppression rules

Low-quality single-source evidence cannot produce high confidence.

## Suppression rules
Candidates are marked `advisory_rejected` for cases like:
- insufficient evidence count
- weak thematic relevance
- low cross-source support
- generic mega-cap contamination patterns

Evidence rows remain persisted for auditability.

## Fallback mode
If Tavily is not available, pipeline still succeeds in deterministic fallback mode and remains non-blocking.

## Artifacts/logs
- `logs/tier3h4_dynamic_entity_discovery_summary.json`
- `logs/tier3h4_dynamic_entity_evidence_summary.json`
- `logs/tier3h4_dynamic_entity_discovery_validation.json`

Evidence summary contains: Tavily enabled flag, fallback mode, queries generated, evidence collected/persisted, top domains, failure count, and suppression totals.

## Operational risk notes
- Search-result quality drift can alter evidence quality distribution.
- Domain-tier lists require periodic maintenance.
- Upstream schema drift may degrade seed quality; fallback path mitigates hard failures.

## Tier 3H.4B.1 — Tavily Operational Controls

This tier adds deterministic and advisory-safe operational governance for paid Tavily usage:

- **Config caps via env + defaults**: query/run caps, per-theme caps, retries, result limits, timeout, and cache lookback.
- **Deterministic query deduplication**: whitespace/case-normalized dedup, no duplicate execution within a run.
- **Lightweight evidence cache reuse**: checks recent evidence (`QUERY_CACHE_LOOKBACK_DAYS`) by `(theme_name, query_text)` and reuses rows with `cache_reused=true`.
- **Graceful fallback**: quota/rate/auth/unavailable/timeout/invalid responses never hard-fail the workflow; deterministic fallback evidence path remains active.
- **Retry governance**: bounded retries with deterministic backoff on transient errors only; no retry on auth/quota/permanent failures.
- **Operational telemetry**: one row per run in `public.tier3h_operational_api_usage` with usage/fallback/retry/quota counters.
- **Operational artifact**: `logs/tier3h4_operational_controls_summary.json` records generated/dedup/executed queries, cache behavior, fallback/quota flags, and execution timing.

### Quota exhaustion handling
When quota is exhausted, remaining queries automatically use deterministic fallback evidence for advisory continuity. The pipeline remains non-blocking and auditable.

### Advisory continuity guarantees
These controls do not alter advisory-only boundaries:
- no monitored-universe writes
- no autonomous actions
- no OpenAI/LLM calls

### Future direction (non-implemented)
A future evidence-lake layer can extend cache retention and lineage across runs, but 3H.4B.1 intentionally keeps cache logic lightweight and reversible.
