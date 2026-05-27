# HIST-DENSITY-1 Pilot 90d Execution Attempt Report

- Date: 2026-05-27 (UTC)
- Requested mode: `real_ops_hist1`
- Requested window: 90 trading days
- Requested symbols: 50
- Output root: `reports/hist_density1_pilot_90d`

## Re-attempt outcome
A second execution attempt was performed after instruction that the FMP key had been added.

Execution command (first attempt):
- `python scripts/run_hist_density1_controlled_historical_density.py --density-mode real_ops_hist1 --trading-days 90 --symbol-count 50 --output-root reports/hist_density1_pilot_90d`
- Result: `ModuleNotFoundError: No module named 'transmission_layers'`

Execution command (second attempt with module path):
- `PYTHONPATH=. python scripts/run_hist_density1_controlled_historical_density.py --density-mode real_ops_hist1 --trading-days 90 --symbol-count 50 --output-root reports/hist_density1_pilot_90d`
- Result: `RuntimeError: FMP_API_KEY missing; OPS-HIST-1 fails closed`

## Pre-run validation summary
- `FMP_API_KEY` availability via OPS-HIST-1 path: **FAILED (still missing in process environment)**.
- Deterministic universe load: **PASSED** (`50` symbols, sorted deterministic ordering).
- OPS-HIST-1 chunking bound: **PASSED** (`MAX_HIST_WINDOW_DAYS=90`, bounded to one chunk for 90d).
- Output directory creation: **PASSED**.

## Failure classification
- Primary category: **API/runtime-related** (secret unavailable to runtime environment)
- Secondary category: **compatibility/execution-environment-related** (`PYTHONPATH` needed for direct script invocation)
- Governance impact: **governance-safe fail closed confirmed**
- Determinism impact: none
- Artifact-volume impact: none

## Bounded corrective actions
1. Export secret into the execution environment where the process runs:
   - `export FMP_API_KEY='<value>'`
2. Re-run with explicit module path:
   - `PYTHONPATH=. python scripts/run_hist_density1_controlled_historical_density.py --density-mode real_ops_hist1 --trading-days 90 --symbol-count 50 --output-root reports/hist_density1_pilot_90d`
3. Keep all governance boundaries unchanged (no replay/prediction/orchestration/streaming/topology activation).
