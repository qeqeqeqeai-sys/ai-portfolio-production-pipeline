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
