from __future__ import annotations

import argparse
import json
from pathlib import Path

from transmission_layers.expectation_failure.real_data.hist_density1_controlled_historical_density_expansion import (
    DEFAULT_SYMBOL_COUNT,
    DEFAULT_TRADING_DAYS,
    DENSITY_MODE_FIXTURE,
    DENSITY_MODE_REAL,
    render_hist_density1_markdown,
    run_hist_density1,
)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--trading-days", type=int, default=DEFAULT_TRADING_DAYS)
    p.add_argument("--symbol-count", type=int, default=DEFAULT_SYMBOL_COUNT)
    p.add_argument("--output-root", default="reports/hist_density1")
    p.add_argument("--start-date", default=None)
    p.add_argument("--end-date", default=None)
    p.add_argument("--density-mode", choices=[DENSITY_MODE_REAL, DENSITY_MODE_FIXTURE], default=DENSITY_MODE_REAL)
    args = p.parse_args()
    payload = run_hist_density1(
        trading_days=args.trading_days,
        symbol_count=args.symbol_count,
        output_root=args.output_root,
        start_date=args.start_date,
        end_date=args.end_date,
        density_mode=args.density_mode,
    )
    Path("reports").mkdir(exist_ok=True)
    Path("reports/hist_density1_controlled_historical_density_expansion.md").write_text(render_hist_density1_markdown(payload), encoding="utf-8")
    Path("reports/hist_density1_controlled_historical_density_expansion.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "density_mode": payload["data_source_mode"], "execution_id": payload["execution_id"], "artifact_count": payload["artifact_count"]}, sort_keys=True))


if __name__ == "__main__":
    main()
