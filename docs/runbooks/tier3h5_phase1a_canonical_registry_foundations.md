# Tier 3H.5 Phase 1A Runbook: Canonical Registry Foundations

## Purpose
Tier 3H.5 Phase 1A provides a deterministic, replayable institutional issuer/security registry foundation separated from Tier 3H.4.

## Execute
- Local entrypoint:
  - `python -m transmission_layers.asset_discovery.tier3h5.canonical_registry_ingestion`
- CI workflow:
  - `.github/workflows/tier3h5_registry_foundations.yml`

## Observable outputs
- Console diagnostics prefixed with `[tier3h5]`.
- Summary file: `logs/tier3h5_registry_foundation_summary.json`.
- Required counters in summary:
  - `issuer_rows_upserted`
  - `security_rows_upserted`
  - `provenance_rows_inserted`
  - `normalization_failures`
  - `deterministic_id_collisions`

## Governance boundaries
- Tier 3H.4 remains frozen; Tier 3H.5 execution is independent.
- No fuzzy matching, LLM logic, ranking heuristics, or probabilistic scoring.
