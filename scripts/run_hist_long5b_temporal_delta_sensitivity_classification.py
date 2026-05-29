from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.expectation_failure.real_data.hist_long5b_temporal_delta_sensitivity_classification import (
    COMPLETED_SOURCE_ARTIFACT_ENV,
    DEFAULT_ARTIFACT_PATH,
    DEFAULT_REPORT_PATH,
    DEFAULT_SOURCE_ARTIFACT_PATH,
    write_hist_long5b,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run HIST-LONG-5B temporal delta sensitivity classification from HIST-LONG-4 artifact")
    parser.add_argument("--source-artifact-path", default=DEFAULT_SOURCE_ARTIFACT_PATH, help="Default HIST-LONG-4 source artifact path")
    parser.add_argument("--completed-source-artifact-path", default=None, help=f"Explicit verified completed HIST-LONG-4 artifact path; overrides --source-artifact-path and {COMPLETED_SOURCE_ARTIFACT_ENV}")
    parser.add_argument("--report-path", default=DEFAULT_REPORT_PATH)
    parser.add_argument("--artifact-path", default=DEFAULT_ARTIFACT_PATH)
    args = parser.parse_args()
    artifact = write_hist_long5b(
        source_artifact_path=args.source_artifact_path,
        completed_source_artifact_path=args.completed_source_artifact_path,
        report_path=args.report_path,
        artifact_path=args.artifact_path,
    )
    print(f"HIST-LONG-5B status={artifact['status']} completed_windows={artifact['completed_windows']}")


if __name__ == "__main__":
    main()
