# PARA Replacement Decision

- Replaced symbol: `PARA`
- Selected replacement: `FOXA`
- WBD preference result: rejected because `WBD` already exists in the curated 241-symbol universe.
- Decision reason: HIST-DENSITY-4 completed telemetry identified `PARA` as the only clear weak/problematic symbol, with repeated FMP historical coverage failures (`HTTP_403` and `zero_records_returned`) across 20 dates.

## Validation

- Bounded live FMP endpoint validation requested 5 trading days against the historical price endpoint and profile endpoint with no Supabase writes, no replay activation, no topology activation, and no trading activation.
- Live FMP endpoint validation was blocked by the execution environment: no `FMP_API_KEY` was present and outbound HTTPS tunnel attempts returned `403 Forbidden` for both endpoint families.
- Short bounded validation backfill completed in synthetic fixture mode with 5 trading days, 241 symbols, symbol chunk size 50, and expected chunk count 5.
- Short validation backfill status: `ok`.
- Short validation backfill failure reasons: none.

## Final Universe Checks

- `PARA` no longer appears in the curated universe.
- `FOXA` appears exactly once.
- Duplicate symbols: none.
- Governance remains observational-only with Supabase writes, replay activation, topology activation, and trading activation disabled.
