from __future__ import annotations

import argparse
import json

from transmission_layers.expectation_failure.real_data.hist_density2_longitudinal_ecology_enrichment import run_hist_density2
from transmission_layers.expectation_failure.real_data.hist_density1_controlled_historical_density_expansion import DENSITY_MODE_FIXTURE, DENSITY_MODE_REAL


def main() -> None:
    p = argparse.ArgumentParser(description="Run HIST-DENSITY-2 180d / 50 symbol pilot")
    p.add_argument("--trading-days", type=int, default=180)
    p.add_argument("--symbol-count", type=int, default=50)
    p.add_argument("--end-date", default=None)
    p.add_argument("--output-root", default="reports/hist_density2_pilot_180d")
    p.add_argument("--density-mode", choices=[DENSITY_MODE_REAL, DENSITY_MODE_FIXTURE], default=DENSITY_MODE_REAL)
    args = p.parse_args()
    payload = run_hist_density2(trading_days=args.trading_days, symbol_count=args.symbol_count, end_date=args.end_date, output_root=args.output_root, density_mode=args.density_mode)
    print(json.dumps({"status": payload["status"], "execution_id": payload["execution_id"]}, sort_keys=True))


if __name__ == "__main__":
    main()
