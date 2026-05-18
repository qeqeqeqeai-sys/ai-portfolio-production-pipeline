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
