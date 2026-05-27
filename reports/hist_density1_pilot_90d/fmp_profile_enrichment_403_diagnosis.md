# FMP Profile Enrichment 403 Diagnosis (HIST-DENSITY-1)

## Exact failure observed
The 90-day HIST-DENSITY-1 pilot failed in `ops_hist1_controlled_historical_observation.py` at profile enrichment fetch time with `HTTP Error 403: Forbidden` from:

- `https://financialmodelingprep.com/api/v3/profile/{comma_joined_symbols}?apikey=...`

## Likely cause
The legacy multi-symbol `/api/v3/profile/{symbols}` path appears plan-restricted/legacy/unsupported for this usage profile in GitHub Actions. The historical adapter treated this profile call as fatal, which is incorrect for backfill where price rows are the required dependency.

## Behavior change implemented
- Profile enrichment is now **optional best-effort** in OPS-HIST-1 historical fetch mode.
- Profile calls now use bounded per-symbol stable endpoint usage:
  - `https://financialmodelingprep.com/stable/profile?symbol=<SYMBOL>&apikey=...`
- Profile failures (403/404/timeout/etc.) no longer fail the snapshot.
- On profile failure, rows continue with:
  - `sector="unknown"`
  - `industry="unknown"`

## Fallback and diagnostics
When profile enrichment fails, diagnostics now include bounded fields:
- `profile_enrichment_status="failed"`
- `profile_records_returned=0` (or bounded returned count)
- `profile_fetch_failure_count`
- `profile_fetch_failure_reasons` (e.g., `HTTP_403`)
- `sector_industry_fallback_used=True`
- `profile_endpoint_status="degraded"`

Additional OPS-HIST-1 diagnostics include:
- `historical_adapter_mode`
- `fmp_endpoint_family_used`
- `historical_price_endpoint_status`
- `historical_market_cap_endpoint_status`
- `profile_endpoint_status`
- `profile_records_requested`
- `profile_records_returned`
- `symbol_count_requested`
- `symbol_count_returned_raw`
- `symbol_count_normalized`
- `normalization_failure_count`
- `top_normalization_failure_reasons`
- `sector_unknown_count`
- `industry_unknown_count`

## Why price data still fails closed
Fail-closed behavior remains for core historical requirements:
- no normalized rows
- all rows missing price (`adjClose`/`close` -> `price`)

So optional profile metadata does not mask empty/invalid historical price snapshots.

## Cache behavior
Added in-memory profile cache keyed by symbol in the historical fetcher closure:
- profile fetched once per symbol per run/chunk
- reused across dates in the same run/chunk
- no persistent storage

## Governance confirmation
No synthetic fallback added for real OPS-HIST-1 mode. No Supabase writes, repo writeback, orchestration, queues, streaming, replay, topology activation, prediction, or trading logic introduced.

## Recommendation
Re-run the 90-day HIST-DENSITY-1 GitHub Actions pilot. The adapter now preserves fail-closed semantics for price data while decoupling optional profile enrichment from snapshot viability.
