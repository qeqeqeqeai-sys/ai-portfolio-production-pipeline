# HIST-DENSITY-1 Pilot 90d Failure Report

- Date: 2026-05-27 (UTC)
- Requested mode: `real_ops_hist1`
- Requested window: 90 trading days
- Requested symbols: 50
- Output root: `reports/hist_density1_pilot_90d`

## Pre-run validation
- `FMP_API_KEY` availability via OPS-HIST-1 path: **FAILED (missing)**.
- Deterministic universe load: **PASSED** (`50` symbols, sorted deterministic ordering).
- OPS-HIST-1 chunking bound: **PASSED** (`MAX_HIST_WINDOW_DAYS=90`, bounded to one chunk for 90d).
- Output directory creation: **PASSED**.

## Failure point
The run was stopped before invoking historical backfill because OPS-HIST-1 fail-closed governance requires `FMP_API_KEY`.

Expected fail-closed runtime exception if execution is attempted:
`RuntimeError: FMP_API_KEY missing; OPS-HIST-1 fails closed`

## Classification
- Category: **API/runtime-related** (secret missing)
- Governance impact: **governance-safe fail closed confirmed**
- Determinism impact: none
- Artifact-volume impact: none
- OPS-HIST compatibility impact: none

## Bounded corrective action
1. Inject `FMP_API_KEY` into execution environment.
2. Re-run exactly:
   - `python scripts/run_hist_density1_controlled_historical_density.py --density-mode real_ops_hist1 --trading-days 90 --symbol-count 50 --output-root reports/hist_density1_pilot_90d`
3. Keep all existing governance flags and linear bounded execution unchanged.
