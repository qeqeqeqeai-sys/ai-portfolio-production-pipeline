import argparse

from transmission_layers.expectation_failure.real_data.ops_hist1_controlled_historical_observation import (
    DEFAULT_HIST_WINDOW_DAYS,
    run_ops_hist1_historical_backfill,
)

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Run OPS-HIST-1 controlled historical observation backfill")
    p.add_argument("--snapshot-date", required=True)
    p.add_argument("--window-days", type=int, default=DEFAULT_HIST_WINDOW_DAYS)
    p.add_argument("--output-dir", default="reports/ops_hist1_50_symbol_backfill")
    args = p.parse_args()
    out = run_ops_hist1_historical_backfill(snapshot_date=args.snapshot_date, output_dir=args.output_dir, window_days=args.window_days)
    print(out["status"])
