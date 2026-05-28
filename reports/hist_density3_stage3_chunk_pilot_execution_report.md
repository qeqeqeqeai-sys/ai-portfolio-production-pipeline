# Stage 3 — HIST-DENSITY-3 Staged Chunk Pilot (Bounded 50-Symbol Chunk)

## Status
- **Execution status:** FAIL-CLOSED (not executed)
- **Date (UTC):** 2026-05-28
- **Reason:** GitHub Actions dispatch path unavailable in this environment (`gh` CLI not installed) and `FMP_API_KEY` is not present locally.

## Required Stage 3 configuration (as requested)
- trading_days=20
- max_symbols=50
- symbol_chunk_size=50
- raw_cache_enabled=false
- raw_cache_write_enabled=false
- cache_validation_mode=false
- cache_only_validation=false
- include_high_risk_symbols=false
- apply_sde2_replacements=true
- dry_run_config_only=false

## Exact workflow command/input intended
Workflow: `.github/workflows/hist_density3_curated_241_pilot.yml`

Intended `workflow_dispatch` inputs:
```json
{
  "trading_days": "20",
  "max_symbols": "50",
  "symbol_chunk_size": "50",
  "raw_cache_enabled": "false",
  "raw_cache_write_enabled": "false",
  "cache_validation_mode": "false",
  "cache_only_validation": "false",
  "include_high_risk_symbols": "false",
  "apply_sde2_replacements": "true",
  "dry_run_config_only": "false"
}
```

Equivalent local runtime command (requires `FMP_API_KEY`):
```bash
PYTHONPATH=. python scripts/run_hist_density_3_curated_241_pilot.py \
  --trading-days 20 \
  --max-symbols 50 \
  --symbol-chunk-size 50 \
  --output-root reports/hist_density3_curated_241
```

## Preflight verification performed
- Confirmed Stage-3 workflow and inputs exist.
- Confirmed runtime enforces `FMP_API_KEY` presence in workflow.
- Confirmed local environment has no `FMP_API_KEY` set.
- Confirmed GitHub CLI unavailable (`gh: command not found`), preventing dispatch from this runner.

## Boundaries and governance posture
- No execution beyond 50 symbols: **confirmed** (no live execution started)
- No multi-chunk expansion: **confirmed**
- No replay execution: **confirmed**
- No topology activation: **confirmed**
- No cognition/replay/topology persistence: **confirmed**
- No raw cache writes: **confirmed**
- No Supabase writes: **confirmed**

## Runtime & telemetry
- Not available due to fail-closed preflight block.

## Recommendation
- **Hold and fix issues first**: run via GitHub Actions `workflow_dispatch` in a GitHub environment where `FMP_API_KEY` is injected from repository secrets, then collect artifacts for the full Stage 3 report.
