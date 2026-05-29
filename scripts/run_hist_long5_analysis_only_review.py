from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.expectation_failure.real_data.hist_long5_analysis_only_review import (
    DEFAULT_ARTIFACT_PATH,
    DEFAULT_REPORT_PATH,
    DEFAULT_SOURCE_ARTIFACT_PATH,
    write_hist_long5_analysis,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run HIST-LONG-5 analysis-only review from a completed HIST-LONG-4 artifact")
    parser.add_argument("--source-artifact-path", default=DEFAULT_SOURCE_ARTIFACT_PATH)
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH)
    parser.add_argument("--artifact-path", default=DEFAULT_ARTIFACT_PATH)
    args = parser.parse_args()
    artifact = write_hist_long5_analysis(
        source_artifact_path=args.source_artifact_path,
        report_path=args.report_path,
        artifact_path=args.artifact_path,
    )
    print(f"HIST-LONG-5 status={artifact['status']} source_window_count={artifact['source_window_count']}")


if __name__ == "__main__":
    main()
