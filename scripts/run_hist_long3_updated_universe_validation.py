from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.expectation_failure.real_data.hist_long3_updated_universe_validation import write_hist_long3_validation


def main() -> None:
    parser = argparse.ArgumentParser(description="Run HIST-LONG-3 updated universe real validation window")
    parser.add_argument("--output-root", default="reports/hist_long3_updated_universe_validation")
    parser.add_argument("--report-path", default="reports/hist_long3_updated_universe_validation.md")
    parser.add_argument("--artifact-path", default="artifacts/hist_long3_updated_universe_validation.json")
    parser.add_argument("--no-execute-real", action="store_true", help="Build the supervisor artifact from existing local outputs only")
    args = parser.parse_args()
    artifact = write_hist_long3_validation(
        output_root=args.output_root,
        report_path=args.report_path,
        artifact_path=args.artifact_path,
        execute_real=not args.no_execute_real,
    )
    print(json.dumps({"status": artifact["status"], "validation_status": artifact["validation_status"], "hist_long4_justified": artifact["hist_long4_justified"]}, sort_keys=True))


if __name__ == "__main__":
    main()
