from __future__ import annotations

import argparse
import json
from datetime import date

from transmission_layers.expectation_failure.real_data.ops_live1_controlled_ecosystem_ingestion import (
    run_ops_live1a_controlled_fmp_probe,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run OPS-LIVE-1A bounded FMP live probe")
    parser.add_argument("--snapshot-date", default=str(date.today()))
    parser.add_argument("--output", default="reports/ops_live1a_fmp_probe_output.json")
    parser.add_argument("--symbols", default="")
    args = parser.parse_args()

    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()] or None
    report = run_ops_live1a_controlled_fmp_probe(snapshot_date=args.snapshot_date, output_path=args.output, symbols=symbols)
    print(json.dumps({"status": report["status"], "output": args.output, "probe_size": report["probe_size"]}, indent=2))


if __name__ == "__main__":
    main()
