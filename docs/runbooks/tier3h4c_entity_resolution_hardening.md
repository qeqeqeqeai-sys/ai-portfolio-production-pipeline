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
