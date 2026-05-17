# Tier 3H.4C.1 Entity Resolution Hardening (Audit-Only Dry Run)

## Purpose
Add a deterministic, advisory-only entity resolution audit layer after Tier 3H.4B candidate/evidence persistence.

## Advisory-only guarantees
- No candidate promotion.
- No monitored-universe writes.
- No LLM/OpenAI usage.
- No buy/sell logic.
- No scoring model rewrite.

## Inputs
- `tier3h_dynamic_entity_discovery` candidate rows (preferred).
- `tier3h_dynamic_entity_evidence` evidence rows.
- Env vars: `RUN_DATE_SGT`, `THEME_NAME` (default `ai`), `WORKFLOW_RUN_ID`/`GITHUB_RUN_ID`, Supabase credentials.

## Outputs
- Supabase audit table `public.tier3h_entity_resolution_audit`.
- Local artifact `logs/tier3h4c_entity_resolution_summary.json`.

## Suppression rules
- Generic name only.
- Suspicious/ambiguous ticker patterns.
- ETF/company conflict.
- Zero-evidence downgrade.
- Missing exchange downgrade for ambiguous short tickers.

## Confidence bands
- `>=80`: resolved_high_confidence
- `60-79`: resolved_medium_confidence
- `40-59`: unresolved_review
- `<40`: suppressed

## Audit table
See `sql/tier3h_entity_resolution_audit.sql` for full schema and indexes.

## Summary JSON interpretation
The summary includes row counts, confidence status distribution, suppression/ambiguity counters, warnings/errors, and write status.

## Known limitations
- Uses deterministic lexical rules only.
- Relies on available candidate/evidence table columns.
- Missing Supabase env gracefully degrades to local summary-only mode.

## Future guardrail
If LLM classification is added later, LLM output can only be advisory; deterministic validation must confirm before any promotion logic (outside 4C.1 scope).

## Tier 3H.4C.2 Resolution Quality Calibration

### Why 3H.4C.1 suppressed all rows
3H.4C.1 used a single fixed evidence table read path. If that read failed (e.g., 404 on an alternate table name), the resolver had no evidence/exchange context and over-suppressed candidates.

### Source-table fallback behavior
The resolver now performs deterministic fallback discovery for both candidate and evidence tables and records attempted/selected table names plus warnings in `logs/tier3h4c_entity_resolution_summary.json`.

### Canonical registry bootstrap
A static deterministic registry bootstrap is introduced for known AI/semiconductor/cloud entities. It is advisory-only and used solely for calibration. It does not write to, mutate, or promote into the monitored universe.

### Safe exchange inference
Exchange is inferred only when ticker match is exact and unique in the static registry, and only when candidate exchange is missing.

### Revised confidence/status calibration
Scoring now includes registry match/inference and evidence presence; hard suppression remains for unsafe cases (generic names, suspicious tickers, ETF/company conflict).

### Status interpretation
- `resolved_high_confidence`: deterministic strong match with sufficient evidence/registry support.
- `resolved_medium_confidence`: deterministic likely match requiring less caution than unresolved.
- `unresolved_review`: potentially valid but missing critical context (commonly exchange/evidence).
- `suppressed`: unsafe or low-quality mapping blocked by hard safeguards.

### Why LLM is still not used
Tier 3H.4C.2 remains deterministic and auditable with no LLM/OpenAI classification.

### Why registry is not universe promotion
Registry entries are bootstrap hints for advisory resolution only. They do not constitute monitored-universe persistence or candidate promotion.

## Tier 3H.4C.2 Stabilization Patch (Follow-up)

### Root cause of `write_failed:400`
The resolver audit payload included `exchange_confidence_source`, but `public.tier3h_entity_resolution_audit` does not define that column. PostgREST returned HTTP 400 for unknown column payload.

### Persistence fix
- Removed non-schema payload column from audit rows.
- Enforced required columns on every audit row before write:
  - `run_date_sgt`, `resolution_status`, `rules_fired`, `evidence_urls`, `source_count`, `duplicate_group_size`.
- Enforced JSON-serializable shapes for JSONB columns (`rules_fired`, `evidence_urls`) as arrays.
- Added sanitized write diagnostics to summary:
  - `write_error_code`, `write_error_message`, `write_error_details`, `write_error_hint`.

### Embedded evidence mode
Resolver now supports evidence extraction from candidate rows when no separate evidence table is readable.
Evidence-like candidate fields include:
- `evidence_url`, `source_url`, `source_domain`, `evidence_snippet`, `source_title`, `tavily_response`, `evidence_sources`, `source_count`.

### Evidence source diagnostics
`logs/tier3h4c_entity_resolution_summary.json` now includes:
- `evidence_source_mode`: `separate_table`, `embedded_candidate_fields`, `unavailable`.
- `evidence_selected_reason`.
- `failed_evidence_table_attempts` (all attempts preserved, not only the final warning).

### Additional diagnostics for self-serve debugging
The summary now includes:
- `sample_candidate_keys`
- `sample_candidate_fields_present`
- `sample_audit_row_keys`
- `audit_payload_column_count`
- `candidate_table_columns_detected`
- `evidence_table_columns_detected`

### Advisory-only behavior preserved
The resolver remains non-blocking and advisory-only:
- no monitored universe writes
- no candidate promotion
- no LLM classification
- no autonomous mapping
- deterministic exact-match registry inference only

## Tier 3H.4C.3 Deterministic Security Identifier Extraction

This layer is **advisory-only** and **additive-only**. It is upstream of Tier 3H.4C entity resolution and does not write to monitored universe tables.

Policy requirements:
- deterministic-only extraction from explicit `exchange:ticker`, explicit ticker fields, exact alias registry, exact ticker+exchange registry matches.
- no fuzzy matching, no LLM classification, no invented ticker/exchange mappings.
- unresolved/suppressed outcomes are preferred over unsafe inference.

Audit fields added:
`extracted_ticker`, `raw_exchange`, `normalized_exchange`, `security_type`, `canonical_security_id`, `identifier_source`, `identifier_method`, `identifier_confidence`, `identifier_status`, `identifier_explanation`, `identifier_warnings`.

Future LLM suggestions (if introduced) must remain quarantined and require deterministic registry validation before any resolver impact.

## Tier 3H.4C.3 Phase 1 — Stabilize Evidence Table Creation

### Purpose of `public.tier3h_dynamic_entity_evidence`
Create a canonical, advisory-only persisted evidence table that stores normalized evidence rows derived from embedded candidate fields and enables deterministic evidence reuse across runs.

### Advisory-only status
- Evidence writes are additive-only and do not mutate monitored-universe tables.
- No autonomous promotion is triggered by evidence persistence.
- No LLM/fuzzy identifier mapping is performed in this phase.
- `llm_classification_json` may be preserved only as raw evidence context.

### Fallback behavior (non-blocking)
- Resolver first attempts to read from `tier3h_dynamic_entity_evidence`.
- Legacy fallback read order remains:
  1. `tier3h4_dynamic_entity_evidence`
  2. `tier3h_dynamic_discovery_evidence`
  3. `tier3h_entity_evidence`
- If persisted evidence read fails or returns zero rows, resolver falls back to `embedded_candidate_fields`.
- Workflow remains non-blocking; diagnostics capture warnings without failing the run.

### Phase 1 success criterion
- `evidence_rows_read > 0` after evidence persistence (same run or subsequent run).
- `evidence_table_selected = tier3h_dynamic_entity_evidence`.
- `evidence_source_mode = persisted_evidence_table` when rows are available.

## Tier 3H.4C.3 Phase 2 — Deterministic Evidence-Level Identifier Extraction

### Extraction scope and guardrails
- Evidence-level extraction only from explicit evidence (`evidence_text`, `source_title`, `source_url`, `raw_evidence`) and explicit candidate ticker/exchange fields when present.
- No name-only inference, no fuzzy/semantic matching, no LLM mapping.
- If no explicit identifier is present, ticker/exchange remain null and suppression/unresolved fallback remains intact.

### Explicit deterministic patterns
- Exchange+ticker regex forms such as `NASDAQ: NVDA`, `NYSE: IBM`, `NYSE Arca: QQQ`, with optional wrappers like `(NASDAQ: NVDA)` or `[NASDAQ: NVDA]`.
- Symbol field regex forms such as `Ticker: MSFT` and `Symbol: AMD`.
- Isolated uppercase words (e.g., `AI`, `ON`, `OR`, `IT`) are ignored unless part of explicit patterns.

### Exchange normalization
- NASDAQ family (`NASDAQ`, `Nasdaq`, `NasdaqGS`, `Nasdaq Global Select Market`) -> `NASDAQ`
- NYSE family (`NYSE`, `New York Stock Exchange`) -> `NYSE`
- NYSE Arca family (`NYSEARCA`, `NYSE Arca`, `Arca`) -> `NYSEARCA`
- `LSE`, `HKEX`, `SGX`, `TSE` families normalize to those canonical values.
- Raw extracted exchange is preserved separately from normalized exchange.

### Conflict handling
- Evidence identifiers are aggregated per candidate deterministically.
- If all explicit identifiers agree, audit ticker/exchange fields are populated.
- If explicit identifiers conflict, no arbitrary selection is made; candidate is suppressed/unresolved with ambiguity rule metadata.

### Diagnostics added for Phase 2
- `evidence_rows_with_ticker`
- `evidence_rows_with_exchange`
- `explicit_exchange_ticker_regex_count`
- `explicit_symbol_field_regex_count`
- `structured_field_extraction_count`
- `conflicting_evidence_identifier_count`
- `invalid_ticker_pattern_count`
- `evidence_identifier_aggregation_count`
- `evidence_identifier_aggregation_conflict_count`

### Phase 2 success metric
- `rows_with_ticker > 0` and `rows_with_exchange > 0` only when explicit evidence supports those fields.
- `evidence_rows_with_ticker > 0` and `evidence_rows_with_exchange > 0` when explicit identifiers are present in persisted evidence rows.

## Tier 3H.4C.3 Phase 2A — Evidence Content Enrichment

### Purpose
Persist richer, deterministic evidence content so downstream deterministic extraction operates on explicit, identifier-bearing text rather than sparse operational-only strings.

### Separation of concerns
- **Enrichment** composes human-readable evidence text from deterministic source fields already returned by discovery/persistence layers.
- **Extraction** remains a separate deterministic phase that only reads explicit identifiers from evidence text/structured fields.

### Deterministic-only policy (unchanged)
- no LLM/OpenAI extraction
- no semantic ticker/exchange inference
- no fuzzy alias matching
- no hallucinated mappings
- no autonomous promotion
- advisory-only behavior remains unchanged

### Enrichment composition order
1. Source title (including Tavily title when present)
2. Source snippet/content/summary (including Tavily snippet/content when present)
3. Deterministic structured metadata already present in payload
4. Existing operational metadata appendix

### Governance and safety constraints
- `raw_evidence` is preserved and not stripped.
- Provenance fields remain persisted (`source_url`, `source_domain`, `source_title`, `evidence_rank`, `evidence_confidence`, `workflow_run_id`, `run_date_sgt`).
- No monitored-universe writes are introduced.
- Workflow remains non-blocking when evidence is absent or sparse.

### Expected outcomes
- `evidence_text` becomes materially richer and human-readable.
- `enriched_evidence_rows_written > 0` in healthy runs.
- `rows_with_ticker` / `rows_with_exchange` may remain near zero when explicit identifiers are absent.
- Status should remain `ok` with empty `errors` under normal operation.

### Tier 3H.4C.3 Phase 2A wiring/composition fix note
This fix wires deterministic textual evidence composition into final evidence persistence. It does **not** change extraction policy, scoring, promotion, or suppression behavior.

Healthy rerun expectation:
- `evidence_rows_read > 0`
- `evidence_rows_written > 0`
- `evidence_rows_with_title > 0` when source titles are present
- `evidence_rows_with_snippet > 0` when snippet/content fields are present
- `enriched_evidence_rows_written > 0`

## Tier 3H.4C.3 Phase 2B — Source-Level Evidence Persistence

### Purpose
Phase 2B ensures persisted evidence rows are true source-result rows (for example one Tavily result per evidence row), not candidate operational metadata rows.
Persistence now happens immediately at source collection time in Tier 3H.4 dynamic discovery, before candidate-level metadata aggregation.

### Source-level row definition
- One deterministic source result maps to one evidence row.
- `raw_evidence.source_result` contains the explicit source payload (`title`, `url`, `content`/`snippet`/`raw_content`, score/metadata fields when present).
- `raw_evidence.candidate_context` may contain candidate operational metadata, but this is secondary context only.

### Deterministic governance policy
- Additive-only and advisory-only behavior is preserved.
- No LLM/OpenAI extraction added.
- No semantic inference/fuzzy matching for ticker/company/exchange mapping.
- No monitored universe writes.
- Suppression and scoring policy remains unchanged.
- Workflow remains non-blocking when source evidence is absent/sparse.

### Extraction contract
- Deterministic extraction/enrichment must operate only on explicit source text/fields (source title/snippet/content/url and source payload).
- Legacy metadata-only rows are tolerated and counted; they are not repaired or hallucinated.

### Phase 2B diagnostics
- `source_level_evidence_rows_written`
- `candidate_metadata_only_evidence_rows`
- `evidence_rows_with_source_url`
- `evidence_rows_with_source_title`
- `evidence_rows_with_source_content`
- `evidence_rows_with_raw_source_payload`
- `evidence_rows_without_source_payload`
- `sample_source_result_keys`
- `sample_source_titles`
- `sample_source_urls`
- `sample_source_content_preview`

### Healthy rollout expectations
- `source_level_evidence_rows_written > 0`
- `evidence_rows_with_source_url > 0`
- `evidence_rows_with_source_title > 0` when titles exist
- `evidence_rows_with_source_content > 0` when snippet/content exists
- `evidence_rows_with_raw_source_payload > 0`
- `enriched_evidence_rows_written > 0`
- `rows_with_ticker` and `rows_with_exchange` may remain zero when explicit identifiers are absent
- `rows_with_ticker` may still be `0`
- `rows_with_exchange` may still be `0`
- `status = ok`
- `errors = []`
