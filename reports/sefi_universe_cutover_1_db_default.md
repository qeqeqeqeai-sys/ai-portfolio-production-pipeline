# SEFI-UNIVERSE-CUTOVER-1 — DB-default universe source

## Source order
1. Read `public.sefi_observation_universe` through the read-only SEFI observation-universe helper.
2. Validate DB rows before use.
3. Use DB symbols only when all validation gates pass.
4. Otherwise use the existing config / `_effective_symbols()` fallback path.

## Validation gates
DB selection requires all of the following:

- `active_count=241`
- `unique_symbol_count=241`
- `duplicate_count=0`
- `digest=2b25bc53631cdf1f95848fbe8a154cd7edd1aed5f4c52a931aedc1ff63a6c3af`

The fallback config path is also validated against the same count, uniqueness, duplicate, and digest gates before use.

## Compact telemetry
The loader emits only bounded telemetry:

- `universe_source_used=db|config_fallback`
- `universe_count`
- `universe_digest`
- `fallback_reason` when DB is unavailable or invalid
- `bounded_sample_symbols` capped at 5 symbols

No full 241-symbol list is printed by the smoke check or this report.

## Fallback behavior
If DB is empty, unavailable, has the wrong count, contains duplicates, has missing required columns, or fails the expected digest, the loader falls back to the existing config source. If config fallback fails validation, the loader fails closed.

If DB has not yet been loaded, run:

```bash
python scripts/load_sefi_observation_universe.py --execute
```

## No-change boundaries
- `public.ai_stock_universe` remains legacy and was not modified.
- Prediction, trading, signal, replay activation, and topology-persistence logic were not changed.
- Output shapes are preserved; existing telemetry keys remain, with compact source telemetry added.

## Verification
- Unit coverage validates DB-valid selection, invalid-count fallback, digest-mismatch fallback, config fallback count, OPS-LIVE loader compatibility, and absence of `ai_stock_universe` references in cutover files.
- CLI smoke coverage validates DB/default/fallback behavior with compact output only.
