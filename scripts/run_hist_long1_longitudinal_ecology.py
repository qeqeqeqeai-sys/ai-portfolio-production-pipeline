from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.expectation_failure.real_data.hist_density1_controlled_historical_density_expansion import DENSITY_MODE_FIXTURE, DENSITY_MODE_REAL
from transmission_layers.expectation_failure.real_data.hist_long1_longitudinal_ecology import write_hist_long1_review


def main() -> None:
    parser = argparse.ArgumentParser(description="Run HIST-LONG-1 bounded longitudinal ecology accumulation")
    parser.add_argument("--windows", default="20,60,120", help="Comma-separated trading-day windows")
    parser.add_argument("--max-symbols", type=int, default=241)
    parser.add_argument("--chunk-size", type=int, default=50)
    parser.add_argument("--output-root", default="reports/hist_long1_windows")
    parser.add_argument("--report-path", default="reports/hist_long1_longitudinal_ecology_review.md")
    parser.add_argument("--artifact-path", default="artifacts/hist_long1_longitudinal_ecology_review.json")
    parser.add_argument("--end-date")
    parser.add_argument("--density-mode", choices=[DENSITY_MODE_FIXTURE, DENSITY_MODE_REAL], default=DENSITY_MODE_FIXTURE)
    args = parser.parse_args()
    windows = tuple(int(part.strip()) for part in args.windows.split(",") if part.strip())
    artifact = write_hist_long1_review(
        windows=windows,
        max_symbols=args.max_symbols,
        chunk_size=args.chunk_size,
        output_root=args.output_root,
        end_date=args.end_date,
        density_mode=args.density_mode,
        report_path=args.report_path,
        artifact_path=args.artifact_path,
    )
    print(json.dumps({"status": artifact["status"], "artifact_checksum": artifact["artifact_checksum"]}, sort_keys=True))


if __name__ == "__main__":
    main()
