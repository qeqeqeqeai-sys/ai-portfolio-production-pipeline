# FMP Historical Adapter Empty Snapshot Diagnosis

- Exact failure observed: 90 OPS-HIST-1 snapshots generated for 2026-01-22 to 2026-05-27 with `symbols_successfully_normalized=0` and `normalization_completeness=0.0`.
- Endpoint path inspected: OPS-HIST-1 historical backfill previously reused live FMP quote fetch path (`/api/v3/quote/...`) through `build_live_fmp_fetcher`, which is not date-aware.
- Root cause: historical snapshot generation did not pass snapshot date into fetch requests and relied on live-schema expectations; this caused historical normalization mismatches and full-row drop/fail-closed behavior.
- Implemented fix: added date-aware historical FMP adapter using historical daily prices + historical market cap + profile metadata, injected bounded adapter diagnostics, and enforced fail-closed on empty normalized snapshot in real historical mode.
- Remaining limitations: valuation/profitability/leverage fields may be unavailable per historical day from selected endpoints and remain explicitly missing/zero-valued under current normalized schema semantics.
- Why synthetic fallback was not used: run remains in `real_ops_hist1` mode and governance prohibits synthetic fallback in real mode.
- Governance confirmation: fail-closed API key behavior preserved; no Supabase writes, no repo writeback runtime behavior, no orchestration/streaming/prediction/trading activation introduced.
