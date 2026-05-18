# Tier 3H.5 Phase 1B — Deterministic Registry Resolution Support

## Scope and governance boundaries
- This phase introduces **advisory-only** deterministic canonical security registry lookup support.
- Tier 3H.4 remains frozen: no production adjudication, scoring, discovery, or propagation behavior is changed.
- No fuzzy matching, no semantic matching, no issuer-name inference, and no ambiguity auto-resolution are allowed.

## Deterministic resolution rules
`resolve_security_from_registry(ticker, exchange, security_registry, security_type=None)` applies:
1. `normalize_ticker()` on ticker input.
2. `normalize_exchange_code()` on exchange input.
3. Invalid input when normalized ticker or exchange is missing.
4. Exact matching on normalized exchange + normalized ticker only.
5. If `security_type` is provided, exact type narrowing is applied after base match.
6. Exactly one active match -> `accepted`.
7. Zero matches -> `no_match`.
8. Multiple matches -> `conflict` (never silently accepted).

## Resolution output contract
- `resolution_status`: accepted | no_match | conflict | invalid_input
- `resolved_security_id`, `resolved_issuer_id`
- `normalized_ticker`, `normalized_exchange`
- `matched_source_registry`
- `match_rule`
- `explanation`
- `conflict_count`, `candidate_count`

## Observability
Execution emits `[tier3h5]` diagnostics and writes:
- `logs/tier3h5_registry_resolution_summary.json`

Summary fields include:
- `registry_resolution_attempts`
- `registry_resolution_accepted`
- `registry_resolution_no_match`
- `registry_resolution_conflicts`
- `registry_resolution_invalid_input`
- `exact_exchange_ticker_matches`
- `exact_exchange_ticker_security_type_matches`
- `deterministic_resolution_failures`
- `status`

## Independent execution
Run:

```bash
python -m transmission_layers.asset_discovery.tier3h5.canonical_registry_resolution
```

When no database path is configured, fixture-based records are used to preserve deterministic, replayable behavior.

## Deferred to later phases
- authoritative overrides
- ADR continuity handling
- issuer graphing
- ownership mapping
- fuzzy/semantic/LLM matching
- Tier 3H.4 production integration
