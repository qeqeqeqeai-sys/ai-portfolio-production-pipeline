# Tier 3H.5 Phase 1C — Registry Coverage Expansion

## Scope
Phase 1C expands **fixture-only** deterministic registry coverage while preserving advisory-only Tier 3H.5 behavior and keeping Tier 3H.4 decoupled.

## Governance boundaries preserved
- No live API connectivity.
- No Tier 3H.4 production adjudication coupling.
- No ADR continuity logic.
- No historical symbol continuity.
- No issuer graphing.
- No fuzzy/semantic/LLM matching.
- No heuristic ranking.

## Fixture expansion
Expanded static fixture set now includes:
- `AAPL / NASDAQ / equity`
- `MSFT / NASDAQ / equity`
- `IBM / NYSE / equity`
- `NVDA / NASDAQ / equity`
- one deliberate duplicate (`AAPL / NASDAQ / equity` duplicate row)
- one deliberate conflict/ambiguous case (`AAPL / NASDAQ` with different `security_type`/`issuer` identity)

## Deterministic ingestion expectations
`logs/tier3h5_registry_foundation_summary.json` retains and validates:
- `records_seen`
- `records_accepted`
- `records_rejected`
- `duplicate_records_detected`
- `conflict_records_detected`
- `issuer_rows_upserted`
- `security_rows_upserted`
- `provenance_rows_inserted`
- `deterministic_id_collisions`
- `normalization_failures`
- `status`

Duplicates are counted deterministically. Conflicts are surfaced and counted, never silently accepted.

## Deterministic resolution expectations
`logs/tier3h5_registry_resolution_summary.json` retains and validates:
- `registry_resolution_attempts`
- `registry_resolution_accepted`
- `registry_resolution_no_match`
- `registry_resolution_conflicts`
- `registry_resolution_invalid_input`
- `exact_exchange_ticker_matches`
- `exact_exchange_ticker_security_type_matches`
- `deterministic_resolution_failures`
- `status`

Ambiguous multi-match scenarios return `conflict`. No fuzzy fallback, no inferred exchange, and no issuer-name matching are introduced.

## Validation
Run:

```bash
python -m pytest -q tests/test_tier3h5_registry_ingestion.py tests/test_tier3h5_registry_resolution.py
```

This phase remains fixture-only and advisory-only by design.
