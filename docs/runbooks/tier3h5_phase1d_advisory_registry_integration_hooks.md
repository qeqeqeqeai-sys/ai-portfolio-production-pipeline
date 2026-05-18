# Tier 3H.5 Phase 1D — Advisory Registry Integration Hooks

Phase 1D adds an **advisory-only** and **diagnostic-only** side-channel registry lookup hook for Tier 3H.4 outputs.

## Feature flag
- `TIER3H5_ADVISORY_REGISTRY_ENABLED` (default disabled)
- strict true parsing: `1`, `true`, `yes`
- all other values are false

## Integration philosophy
- Hook runs after Tier 3H.4 discovery/adjudication output generation.
- Hook emits telemetry only and does not mutate acceptance, confidence, propagation, reconciliation, suppression, or canonical outputs.
- Exact deterministic matching only: `exchange+ticker` and `exchange+ticker+security_type`.

## Summary output
- `logs/tier3h5_advisory_registry_summary.json`
- deterministic fields include enablement, attempts, exact matches, conflicts, no-match counts, invalid-input counts, support aggregates, failures, and status.

## Freeze boundary
Tier 3H.4 behavior remains frozen: no enforcement, no canonical override, no fuzzy/semantic/LLM matching. Any future enforcement remains intentionally deferred.

## Phase 2A coverage extension (deterministic-only)
- Added centralized canonical normalization for ticker, exchange, and security type with normalization versioning.
- Exchange aliases are deterministic exact canonicalizations only (for example `NYSEARCA|ARCA|AMEX -> ARCA`, `NASDAQGS|NASDAQGM|NASDAQ -> NASDAQ`).
- Security types now include `ETF`, `ADR`, `REIT`, `preferred_share`, `warrant`, and `unit` in addition to existing supported types.
- Added advisory telemetry/ingestion diagnostics for coverage ratios, unsupported candidates, exchange/security coverage breakdowns, and normalization failure counts.
- Governance preserved: no advisory enforcement, no scoring mutation, no propagation mutation, no canonical overwrite behavior.
