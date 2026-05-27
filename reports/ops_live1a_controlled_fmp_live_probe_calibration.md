# OPS-LIVE-1A — Controlled FMP Live Probe & Field Mapping Calibration

## Objective
Calibrate real FMP ingestion through the OPS-LIVE-1 hardened adapter/validation path using a deterministic bounded probe universe, with local dry-run output only.

## Probe Universe
Default bounded probe universe (max 10): `AAPL, MSFT, JPM, XOM, UNH, PG, NEM, NEE`.
Configurable through script `--symbols`, still bounded to `MAX_PROBE_UNIVERSE_SIZE`.

## FMP Field Mapping Table
- `price -> price_state`
- `marketCap -> market_cap`
- `sector -> sector`
- `industry/subsector -> subsector`
- `volatility/beta -> volatility_structure`
- `valuation/pe -> valuation_structure`
- `profitability/roe -> profitability_structure`
- `leverageLiquidity/debtToEquity -> leverage_liquidity_structure`
- `breadthDispersion/dispersion -> breadth_dispersion_structure`

## Diagnostics Design
Probe output diagnostics include:
- mapped fields by symbol
- missing fields
- null fields
- fallback fields used
- invalid numeric/financial values
- symbols failed closed
- symbols successfully normalized

## Dry-Run and Local Output Behavior
- Reads `FMP_API_KEY` from environment only (fails closed if absent).
- Probe-only bounded execution.
- Local JSON report output only.
- No Supabase writes by default.
- Uses OPS-LIVE-1 adapter and integrity validation path.

## Payload Shape Verification
Probe report captures these operator payload surfaces:
- `daily_ecosystem_posture`
- `dominant_structural_pressures`
- `strongest_resilience_pathways`
- `fragmentation_hotspots`
- `transition_state_summaries`
- `continuity_summaries`
- `normalization_observations`
- `compression_observability`

## Snapshot Identity Verification
Probe report includes:
- deterministic `snapshot_ts`
- `snapshot_id`
- `symbol_checksum`
- `row_checksum`

## Test Summary
Added deterministic tests for:
- successful mapping
- missing optional/required handling and fail-closed behavior
- null/NaN/negative invalid handling
- bounded probe size
- no DB write path by default
- payload shape stability
- governance boundary preservation

## Governance Certification
- `observational_only = True`
- `no_recursive_replay_operationalization = True`
- `no_autonomous_replay = True`
- `no_topology_activation = True`
- `no_self_modifying_pathways = True`
- `no_prediction_or_trading_execution = True`
- `no_graph_execution_engines = True`
- `no_high_frequency_streaming = True`

## Recommendation
Proceed to OPS-LIVE-1B 50-symbol controlled ingest only after at least one successful live probe execution with all required fields passing integrity validation and no fail-closed symbols for required fields.
