# FMP Historical Price 403 Diagnosis (HIST-DENSITY-1 90-day pilot)

## Exact failure observed
GitHub Actions failed in `ops_hist1_controlled_historical_observation.py` during historical price fetch with:

- `urllib.error.HTTPError: HTTP Error 403: Forbidden`
- failing path previously used legacy URL construction under `/api/v3/historical-price-full/{symbol}`.

## Root cause / strongest finding
The historical price path relied on legacy endpoint usage and brittle URL construction. The previous behavior exposed risk for malformed query composition and endpoint-family drift (including observed malformed fragments like `?hp_d` in trace context), causing FMP request rejection (HTTP 403).

## Old endpoint/URL shape
- Legacy family: `https://financialmodelingprep.com/api/v3/historical-price-full/{SYMBOL}?from=YYYY-MM-DD&to=YYYY-MM-DD&apikey=***`
- Vulnerability: manual/unsafe composition patterns and legacy family coupling.

## New endpoint/URL shape (no secret values)
- Primary stable family: `https://financialmodelingprep.com/stable/historical-price-eod/full?symbol={SYMBOL}&from={YYYY-MM-DD}&to={YYYY-MM-DD}&apikey=***`
- Built with `urllib.parse.urlencode` via `_build_fmp_url(...)`.

## Diagnostics added
OPS-HIST-1 adapter diagnostics now include bounded, non-secret fields:

- `historical_price_endpoint_family`
- `primary_endpoint_family`
- `fallback_endpoint_family`
- `historical_price_url_shape_valid`
- `historical_price_query_parameters_present`
- `historical_price_endpoint_status`
- `historical_price_http_status_counts`
- `historical_price_failure_reasons`
- `historical_price_records_requested`
- `historical_price_records_returned`
- `historical_price_records_matched_to_snapshot_date`
- `historical_price_symbols_succeeded`
- `historical_price_symbols_failed`
- `sample_historical_price_raw_keys_observed`
- `historical_market_cap_endpoint_status`
- `profile_enrichment_status`

## Why historical price remains required
Historical price is a required input for OPS-HIST-1 normalization and continuity observation. If all symbols fail price fetch, OPS-HIST-1 now fails closed with explicit runtime error and bounded reason metadata.

## Why synthetic fallback is not used
Synthetic price fallback is intentionally disallowed in `real_ops_hist1` governance boundaries to preserve real-data integrity and avoid fabricated market observations.

## Governance confirmation
Confirmed unchanged:

- no synthetic fallback in real mode
- no API key logging
- no Supabase writes
- no repo writeback
- no orchestration/streaming/replay/topology activation/prediction/trading logic introduced

## Recommendation
Rerun the 90-day HIST-DENSITY-1 GitHub Actions pilot. The malformed/legacy historical price URL path has been replaced with stable endpoint-safe construction and bounded diagnostics for any residual plan-level 403s.
