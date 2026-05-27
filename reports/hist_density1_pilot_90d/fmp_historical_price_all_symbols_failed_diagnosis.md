# HIST-DENSITY-1 90D Pilot: Historical Price All-Symbol Failure Diagnosis

## Exact failure observed
`RuntimeError: OPS-HIST-1 fails closed: all symbols failed historical price fetch` during real OPS-HIST-1 historical observation generation.

## Likely causes addressed
- Stable endpoint response envelope mismatch (list vs dict/historical/data/results/symbol-keyed/object).
- Single-day `from=to` fetch returning empty records on non-trading/day-alignment boundaries.
- Strict exact-date selection rejecting valid nearby prior trading rows.
- Stable endpoint family access inconsistency requiring bounded deterministic fallback.

## Endpoint fallback strategy implemented
Deterministic bounded endpoint probing per symbol:
1. `stable_historical_price_eod_full` (`/stable/historical-price-eod/full?symbol=...`)
2. `stable_historical_price_eod_light` (`/stable/historical-price-eod/light?symbol=...`)
3. `legacy_historical_price_full` (`/api/v3/historical-price-full/<symbol>?...`)

Fallback occurs only on HTTP error, malformed/unsupported payload, zero records, missing reconciled date, or missing price field.

## Bounded lookback window policy
Historical fetch window expanded to:
- `from = snapshot_date - 7 calendar days`
- `to = snapshot_date`

This preserves bounded behavior while covering holidays/non-trading gaps.

## Date reconciliation policy
Selection rule:
- prefer exact `snapshot_date`
- if missing, select nearest prior record within <= 5 calendar days
- no future-date selection
- if none found within bound, fail symbol with `missing_reconciled_historical_date`

Diagnostic fields include reconciliation metadata and distance.

## Diagnostics added
Per-attempt bounded diagnostics include:
- endpoint family
- HTTP status classification
- top-level response type and bounded keys
- bounded record count, sample record keys, sample returned dates
- requested date, exact match flag, selected record date
- bounded failure reason

All-symbol fail-closed error now includes bounded endpoint status counts and top failure reasons.
No API key or full payload/secret URL logging.

## Why historical price remains required
Historical price remains required input for OPS-HIST-1 normalization continuity semantics. If all symbols fail price fetch, OPS-HIST-1 must fail closed to prevent invalid historical continuity outputs.

## Why synthetic fallback is not used
Synthetic price fallback is intentionally disallowed in `real_ops_hist1` mode to preserve data provenance and governance guarantees.

## Governance confirmation
No Supabase writes, no repo writeback behavior change, no orchestration/streaming/replay/topology activation/prediction/trading logic introduced.
Profile enrichment remains optional/non-fatal; market cap remains optional/non-fatal if price exists.

## Recommendation
Rerun the 90-day GitHub Actions HIST-DENSITY-1 pilot with the updated adapter and inspect bounded adapter diagnostics for endpoint-family success distribution and residual symbol-level failures.
