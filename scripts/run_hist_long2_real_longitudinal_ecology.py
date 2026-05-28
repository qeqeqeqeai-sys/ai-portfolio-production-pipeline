from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.expectation_failure.real_data.hist_long2_real_longitudinal_ecology import write_hist_long2_review


def main() -> None:
    parser = argparse.ArgumentParser(description="Run HIST-LONG-2 real longitudinal ecology artifact ingestion")
    parser.add_argument("--execute-real-windows", action="store_true", help="Optionally run bounded real windows before comparison")
    parser.add_argument("--end-date")
    parser.add_argument("--output-root", default="reports/hist_long2_windows")
    parser.add_argument("--report-path", default="reports/hist_long2_real_longitudinal_ecology_review.md")
    parser.add_argument("--artifact-path", default="artifacts/hist_long2_real_longitudinal_ecology_review.json")
    args = parser.parse_args()
    artifact = write_hist_long2_review(
        execute_real_windows=args.execute_real_windows,
        output_root=args.output_root,
        end_date=args.end_date,
        report_path=args.report_path,
        artifact_path=args.artifact_path,
    )
    print(f"HIST-LONG-2 status={artifact['status']} real_completed_telemetry_used={artifact['real_completed_telemetry_used']} new_real_execution_run={artifact['new_real_execution_run']}")


if __name__ == "__main__":
    main()
