import argparse

from transmission_layers.expectation_failure.real_data.ops_live1_controlled_ecosystem_ingestion import (
    run_ops_live1b_controlled_50_symbol_operational_ingest,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run OPS-LIVE-1B controlled 50-symbol operational ingest")
    parser.add_argument("--snapshot-date", required=True)
    parser.add_argument("--output", default="reports/ops_live1b_50_symbol_operational_ingest_output.json")
    args = parser.parse_args()
    out = run_ops_live1b_controlled_50_symbol_operational_ingest(snapshot_date=args.snapshot_date, output_path=args.output)
    print(out["status"])


if __name__ == "__main__":
    main()
