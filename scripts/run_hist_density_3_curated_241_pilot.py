from __future__ import annotations
import argparse, json
from transmission_layers.expectation_failure.real_data.hist_density1_controlled_historical_density_expansion import DENSITY_MODE_REAL
from transmission_layers.expectation_failure.real_data.hist_density3_curated_ecology_expansion import run_hist_density3

def main() -> None:
    p = argparse.ArgumentParser(description="Run HIST-DENSITY-3 curated 241 symbol pilot")
    p.add_argument("--trading-days", type=int, default=180)
    p.add_argument("--max-symbols", type=int, default=241)
    p.add_argument("--symbol-chunk-size", type=int, default=50)
    p.add_argument("--raw-cache-enabled", action="store_true")
    p.add_argument("--raw-cache-write-enabled", action="store_true")
    p.add_argument("--cache-validation-mode", action="store_true")
    p.add_argument("--cache-only-validation", action="store_true")
    p.add_argument("--include-high-risk-symbols", action="store_true")
    p.add_argument("--apply-sde2-replacements", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--dry-run-config-only", action=argparse.BooleanOptionalAction, default=False)
    p.add_argument("--output-root", default="reports/hist_density3_curated_241")
    args = p.parse_args()
    payload = run_hist_density3(trading_days=args.trading_days, max_symbols=args.max_symbols, symbol_chunk_size=args.symbol_chunk_size, raw_cache_enabled=args.raw_cache_enabled, raw_cache_write_enabled=args.raw_cache_write_enabled, cache_validation_mode=args.cache_validation_mode, cache_only_validation=args.cache_only_validation, include_high_risk_symbols=args.include_high_risk_symbols, apply_sde2_replacements=args.apply_sde2_replacements, dry_run_config_only=args.dry_run_config_only, output_root=args.output_root, density_mode=DENSITY_MODE_REAL)
    print(json.dumps({"status": payload.get("status", "ok")}, sort_keys=True))

if __name__ == "__main__":
    main()
